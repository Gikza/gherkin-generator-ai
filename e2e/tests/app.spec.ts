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

test.describe('Respuestas a las preguntas de aclaración', () => {
  const ambigua = 'Como usuario quiero buscar productos. La búsqueda debe ser rápida.';

  test('genera escenarios después de responder las preguntas', async ({ page }) => {
    await generar(page, ambigua);

    const respuesta = page.getByLabel('Pregunta 1: ¿Cuál es el tiempo máximo de respuesta?');
    await respuesta.fill('2 segundos');
    await respuesta.press('Enter');
    await page.getByRole('button', { name: 'Generar con respuestas' }).click();

    await expect(page.getByText('Sin problemas graves.')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Escenarios' })).toBeVisible();
    await expect(page.getByText('Historia usada (con tus respuestas)')).toBeVisible();
  });

  test('pide al menos una respuesta antes de generar', async ({ page }) => {
    await generar(page, ambigua);

    await page.getByRole('button', { name: 'Generar con respuestas' }).click();

    await expect(page.getByText('Respondé al menos una pregunta antes de generar.')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Escenarios' })).toHaveCount(0);
  });
});

test.describe('Reporte de bug', () => {
  // Pasa a la pestaña de reportes, escribe la descripción y aprieta "Generar reporte".
  async function generarReporte(page: Page, descripcion: string) {
    await page.getByRole('tab', { name: 'Reporte de bug' }).click();
    const cuadro = page.getByLabel('Descripción del bug');
    await cuadro.fill(descripcion);
    await cuadro.press('Control+Enter');
    await page.getByRole('button', { name: 'Generar reporte' }).click();
  }

  test('muestra un error si la descripción está vacía', async ({ page }) => {
    await generarReporte(page, '');
    await expect(page.getByText('Describí el bug antes de generar el reporte.')).toBeVisible();
  });

  // Coincide con ENTRADA_SIMULADA (simulador.py), para que B08 encuentre los datos del reporte.
  const descripcion =
    'Al iniciar sesión con usuario y contraseña válidos aparece "Error 500: Internal Server Error" y no entro a mi cuenta.';

  test('genera el reporte con su validación', async ({ page }) => {
    await generarReporte(page, descripcion);

    await expect(page.getByText('Sin problemas graves.')).toBeVisible();
    for (const regla of ['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08']) {
      await expect(page.getByText(`${regla}: OK`)).toBeVisible();
    }
    await expect(page.getByRole('heading', { name: 'Reporte', exact: true })).toBeVisible();
    await expect(page.getByText('[Login] Iniciar sesión con credenciales válidas').first()).toBeVisible();
  });

  test('descarga el reporte generado', async ({ page }) => {
    await generarReporte(page, descripcion);

    const descarga = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Descargar reporte' }).click();
    const archivo = await descarga;

    expect(archivo.suggestedFilename()).toBe('reporte_bug.md');
    const contenido = readFileSync(await archivo.path(), 'utf-8');
    expect(contenido.startsWith('**Título:**')).toBe(true);
  });

  test('pide datos esenciales y genera después de responder', async ({ page }) => {
    await generarReporte(page, 'El login no anda.');

    await expect(page.getByText('Faltan datos esenciales para redactar el reporte')).toBeVisible();
    const respuesta = page.getByLabel('Pregunta 1: ¿Qué pasa exactamente cuando falla?');
    await respuesta.fill('Aparece un error 500');
    await respuesta.press('Enter');
    await page.getByRole('button', { name: 'Generar con respuestas' }).click();

    await expect(page.getByRole('heading', { name: 'Reporte', exact: true })).toBeVisible();
  });
});

test.describe('Manejo de errores', () => {
  test('muestra un mensaje claro si la IA tarda demasiado', async ({ page }) => {
    await generar(page, 'ERROR_TIMEOUT');
    await expect(page.getByText('La IA tardó demasiado en responder')).toBeVisible();
  });
});
