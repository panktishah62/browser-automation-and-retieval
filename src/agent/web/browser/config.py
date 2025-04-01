class BrowserConfig:
    """Configuration class for browser settings."""
    
    def __init__(self):
        # Default browser type (chromium, firefox, or webkit)
        self.browser_type = "chromium"
        
        # Browser launch options
        self.browser_launch_options = {
            "headless": False,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-position=0,0",
                "--ignore-certifcate-errors",
                "--ignore-certifcate-errors-spki-list",
                "--disable-notifications",
                "--disable-popup-blocking",
                "--disable-translate",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-default-apps",
                "--no-default-browser-check",
                "--no-first-run",
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            ],
        }
        
        # Browser context options
        self.context_options = {
            "viewport": {
                "width": 1280,
                "height": 720
            },
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "ignore_https_errors": True,
            "permissions": ["geolocation"],
            # Add color scheme to match regular browsers
            "color_scheme": "light",
            # Timezone and locale settings
            "timezone_id": "America/New_York",
            "locale": "en-US",
            # Enable JavaScript
            "java_script_enabled": True,
            # Block automatic popups
            "bypass_csp": True,
            # Handle common dialogs automatically
            "accept_downloads": False,
            "has_touch": False,
            "is_mobile": False,
        }
        
        # Navigation timeout in milliseconds
        self.navigation_timeout = 30000
        
        # Wait for element timeout in milliseconds
        self.element_timeout = 10000
