import { defineConfig, devices } from '@playwright/test';

// Python del entorno virtual del proyecto (Windows o Mac/Linux).
const python =
  process.platform === 'win32' ? '.venv\\Scripts\\python.exe' : '.venv/bin/python';

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],

  use: {
    baseURL: 'http://localhost:8502',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },

  // Usa el Google Chrome instalado en la compu. En algunas compus con Windows,
  // el navegador que descarga Playwright queda bloqueado (error "spawn UNKNOWN").
  projects: [{ name: 'chrome', use: { ...devices['Desktop Chrome'], channel: 'chrome' } }],

  // Playwright levanta la app en modo prueba antes de los tests y la cierra al final.
  webServer: {
    command: `${python} -m streamlit run app.py --server.port 8502 --server.headless true`,
    cwd: '..',
    url: 'http://localhost:8502',
    env: { MODO_PRUEBA: '1' },
    timeout: 60_000,
    reuseExistingServer: false,
  },
});
