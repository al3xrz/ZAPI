import aiohttp
import asyncio
from typing import Any, Dict, Optional, List
import logging
import re
from aiohttp import ClientError, ClientResponseError, CookieJar
from urllib.parse import urljoin
import json

logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        # Создаем собственную CookieJar для лучшего управления куками
        # unsafe для работы с любыми доменами
        self.cookie_jar = CookieJar(unsafe=True)

    async def __aenter__(self):
        # Инициализируем сессию с нашей CookieJar
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            cookie_jar=self.cookie_jar,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None

    async def post(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Выполняет POST-запрос к API"""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use async with APIClient()")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            logger.debug(
                "Making POST request to %s with payload: %s", url, payload)

            async with self.session.post(
                url,
                json=payload,
                headers=headers
            ) as response:
                response.raise_for_status()
                result = await response.json()

                logger.debug("Received response from %s: %s", url, result)
                return result

        except ClientResponseError as e:
            logger.error("HTTP error %d for %s: %s", e.status, url, e.message)
            raise
        except asyncio.TimeoutError:
            logger.error("Timeout while requesting %s", url)
            raise
        except ClientError as e:
            logger.error("Connection error for %s: %s", url, str(e))
            raise

    
    
    async def web_login(self, username: str, password: str) -> bool:
        """
        Исправленная версия веб-логина для Zabbix
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with APIClient()")

        try:
            # Шаг 1: Получаем страницу логина
            login_url = urljoin(self.base_url, '/index.php')
            async with self.session.get(login_url, ssl=False) as resp:
                html = await resp.text()
                
                # Ищем CSRF токен и другие скрытые поля
                form_refresh_match = re.search(r'name="form_refresh"\s+value="(\d+)"', html)
                form_refresh = form_refresh_match.group(1) if form_refresh_match else ""
                
                sid_match = re.search(r'name="sid"\s+value="([^"]*)"', html)
                sid = sid_match.group(1) if sid_match else ""

            # Шаг 2: Подготавливаем данные для логина
            payload = {
                "name": username,
                "password": password,
                "enter": "Sign in",
                "form_refresh": form_refresh,
                "autologin": "1",  # Пробуем включить автологин
            }
            
            if sid:
                payload["sid"] = sid

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': login_url,
                'Origin': self.base_url.rstrip('/')
            }

            # Шаг 3: Выполняем POST-запрос с отслеживанием редиректов
            async with self.session.post(
                login_url, 
                data=payload, 
                headers=headers, 
                ssl=False,
                allow_redirects=False  # Сначала отключаем авторедиректы
            ) as resp:
                
                print(f"🔍 POST Login Response: {resp.status}")
                print(f"🔍 Location Header: {resp.headers.get('Location', 'None')}")
                
                # Если есть редирект - следуем за ним
                if resp.status in [301, 302, 303]:
                    redirect_url = resp.headers.get('Location', '')
                    if redirect_url:
                        if not redirect_url.startswith('http'):
                            redirect_url = urljoin(self.base_url, redirect_url)
                        
                        print(f"🔍 Following redirect to: {redirect_url}")
                        async with self.session.get(
                            redirect_url, 
                            ssl=False, 
                            allow_redirects=True
                        ) as redirect_resp:
                            final_url = str(redirect_resp.url)
                            final_status = redirect_resp.status
                            response_html = await redirect_resp.text()
                    else:
                        final_url = str(resp.url)
                        final_status = resp.status
                        response_html = await resp.text()
                else:
                    final_url = str(resp.url)
                    final_status = resp.status
                    response_html = await resp.text()

            # Проверяем куки после всех запросов
            cookies = self.session.cookie_jar.filter_cookies(self.base_url)
            zbx_session_cookie = cookies.get('zbx_session')
            
            print("=" * 50)
            print("🔍 FINAL LOGIN RESULT:")
            print(f"   Final URL: {final_url}")
            print(f"   Final Status: {final_status}")
            print(f"   zbx_session present: {zbx_session_cookie is not None}")
            
            if zbx_session_cookie:
                print(f"   zbx_session value: {zbx_session_cookie.value}")
            
            # Улучшенная проверка успешного логина
            success_indicators = [
                'dashboard' in final_url,
                'zabbix.php' in final_url and 'action=dashboard' in final_url,
                'overview' in final_url,
                'latest' in final_url,
                'Dashboard' in response_html,
                'logout' in response_html,
                'user-profile' in response_html
            ]
            
            failure_indicators = [
                'index.php' in final_url and 'login' in final_url,
                'Login' in response_html,
                'incorrect' in response_html,
                'error' in response_html,
                'Sign in' in response_html
            ]

            # Проверяем наличие сообщения об ошибке в ответе
            if 'incorrect' in response_html.lower():
                print("❌ Ошибка: Неправильное имя пользователя или пароль")
                return False
            
            if any(success_indicators):
                print("✅ Login successful based on page content")
                return True
            elif zbx_session_cookie and not any(failure_indicators):
                print("✅ Login successful based on session cookie")
                return True
            else:
                print("❌ Login failed - no success indicators found")
                print(f"   Success indicators: {[ind for ind in success_indicators if ind]}")
                print(f"   Failure indicators: {[ind for ind in failure_indicators if ind]}")
                return False

        except Exception as e:
            print(f"❌ Error during web login: {str(e)}")
            return False



    async def check_session_valid(self) -> bool:
        """
        Проверяет валидность сессии путем запроса защищенной страницы
        """
        try:
            # Пробуем несколько защищенных URL'ов
            test_urls = [
                '/zabbix.php?action=dashboard.view',
                '/overview.php',
                '/latest.php',
                '/zabbix.php?action=problem.view'
            ]
            
            for test_url in test_urls:
                url = urljoin(self.base_url, test_url)
                async with self.session.get(url, ssl=False, allow_redirects=False) as resp:
                    print(f"🔍 Session check {test_url}: Status {resp.status}")
                    
                    # Если не редирект на логин - сессия валидна
                    if resp.status == 200:
                        html = await resp.text()
                        if 'login' not in html.lower() and 'sign in' not in html.lower():
                            print(f"✅ Session valid (accessed {test_url})")
                            return True
                    elif resp.status in [301, 302]:
                        location = resp.headers.get('Location', '')
                        if 'index.php' in location and 'login' in location:
                            print(f"❌ Session invalid (redirected to login from {test_url})")
                            return False
            
            return False
            
        except Exception as e:
            print(f"❌ Session check error: {str(e)}")
            return False


    async def get_zabbix_chart(
        self,
        itemids: List[int],
        time_from: str = 'now-1h',
        time_till: str = 'now',
        width: int = 800,
        height: int = 200
    ) -> bytes:
        """Получает график из Zabbix через chart.php"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with APIClient()")

        chart_url = urljoin(self.base_url, '/chart.php')
        
        params = {
            'from': time_from,
            'to': time_till,
            'width': width,
            'height': height,
            'profileIdx': "web.item.graph.filter"
        }
        print("параметры запроса", params)
        
        # Добавляем itemids в параметры (правильный формат для Zabbix)
        for i, itemid in enumerate(itemids):
            params[f'itemids[{i}]'] = itemid

        try:
            async with self.session.get(chart_url, params=params, ssl=False) as resp:
                resp.raise_for_status()
                
                # Проверяем, что получили изображение, а не страницу логина
                content_type = resp.headers.get('Content-Type', '')
                if 'text/html' in content_type:
                    response_text = await resp.text()
                    print(response_text)
                    if 'login' in response_text.lower():
                        raise RuntimeError("Session expired - redirected to login page")
                    else:
                        raise RuntimeError(f"Unexpected HTML response: {response_text[:200]}...")
                
                return await resp.read()
                
        except ClientResponseError as e:
            logger.error("HTTP error %d while fetching chart: %s", e.status, e.message)
            raise
        except Exception as e:
            logger.error("Error fetching chart: %s", str(e))
            raise

    async def debug_session(self):
        """Отладочная функция для проверки состояния сессии"""
        if not self.session:
            print("❌ Session not initialized")
            return
            
        cookies = self.session.cookie_jar.filter_cookies(self.base_url)
        print("📋 Current cookies:")
        for name, cookie in cookies.items():
            print(f"  {name}: {cookie.value}")
        
        # Проверяем доступ к дашборду
        dashboard_url = urljoin(self.base_url, '/zabbix.php?action=dashboard.view')
        async with self.session.get(dashboard_url, ssl=False) as resp:
            print(f"🏠 Dashboard access: {resp.status}")
            if resp.status == 200:
                print("✅ Session is valid")
            else:
                print("❌ Session is invalid")
