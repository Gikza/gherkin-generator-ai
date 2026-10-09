import { test, expect, Page } from '@playwright/test';
import { readFileSync } from 'fs';

// Escribe la historia y aprieta "Generar".
// Control+Enter confirma el texto en Streamlit antes de hacer clic.
async function generar(page: Page, historia: string) {
  const cuadro = page.getByLabel('Historia de usuario');
  await cuadro.fill(historia);
  await cuadro.press('Control+Enter');
  await page.getByRole('button', { name: 'Generar', exact: true }).click();
}

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Generador de casos Gherkin' })).toBeVisible();
});

test.describe('Validación de la entrada', () => {
  test('muestra un error si la historia está vacía', async ({ page }) => {
    await page.getByRole('button', { name: 'Generar', exact: true }).click();
    await expect(page.getByText('Pegá una historia de usuario antes de generar.')).toBeVisible();
  });

  test('muestra un error si la historia tiene solo espacios', async ({ page }) => {
    await generar(page, '     ');
    await expect(page.getByText('Pegá una historia de usuario antes de generar.')).toBeVisible();
  });
});

test.describe('Respuesta de la IA', () => {
  test('pide aclaraciones si la historia es ambigua', async ({ page }) => {
    await generar(page, 'Como usuario quiero buscar productos. La búsqueda debe ser rápida.');

    await expect(page.getByText('La historia necesita aclaraciones')).toBeVisible();
    await expect(page.getByText('¿Cuál es el tiempo máximo de respuesta?')).toBeVisible();
    // No debe generar escenarios cuando faltan datos.
    await expect(page.getByRole('heading', { name: 'Escenarios' })).toHaveCount(0);
  });

  test('genera escenarios con su validación', async ({ page }) => {
    await generar(page, 'Como usuario registrado quiero iniciar sesión para acceder a mi cuenta.');

    await expect(page.getByText('Sin problemas graves.')).toBeVisible();
    for (const regla of ['R04', 'R05', 'R07', 'R08', 'R20']) {
      await expect(page.getByText(`${regla}: OK`)).toBeVisible();
    }
    await expect(page.locator('[data-testid="stCode"]')).toContainText('Característica: Inicio de sesión');
  });

  test('descarga el archivo .feature generado', async ({ page }) => {
    await generar(page, 'Como usuario registrado quiero iniciar sesión para acceder a mi cuenta.');

    const descarga = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Descargar .feature' }).click();
    const archivo = await descarga;

    expect(archivo.suggestedFilename()).toBe('casos.feature');
    const contenido = readFileSync(await archivo.path(), 'utf-8');
    expect(contenido.startsWith('# language: es')).toBe(true);
  });
});

test.describe('Manejo de errores', () => {
  test('muestra un mensaje claro si la IA tarda demasiado', async ({ page }) => {
    await generar(page, 'ERROR_TIMEOUT');
    await expect(page.getByText('La IA tardó demasiado en responder')).toBeVisible();
  });
});
