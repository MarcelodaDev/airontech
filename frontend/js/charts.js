// js/charts.js

// Variables globales para almacenar las instancias de los gráficos
// Esto es crucial para poder destruirlos (limpiarlos) antes de dibujar uno nuevo
let univariateChartInstance = null;
let bivariateChartInstance = null;

// Paleta de colores basada en tu CSS (Glassmorphism / Tonos azules)
const chartTheme = {
    primary: 'rgba(44, 125, 160, 0.7)',     // #2c7da0 con transparencia
    primaryBorder: '#2c7da0',
    secondary: 'rgba(31, 80, 104, 0.7)',    // #1f5068
    gridLines: 'rgba(203, 221, 233, 0.5)',  // #cbdde9
    fontFamily: "'Inter', sans-serif"
};

/**
 * Renderiza el gráfico de Exploración Univariada (Pestaña: EDA)
 * @param {Array} labels - Etiquetas del eje X (ej. rangos numéricos o categorías)
 * @param {Array} data - Valores del eje Y (ej. frecuencias)
 * @param {String} type - Tipo de gráfico: 'bar' (histograma) o 'doughnut' (categóricas)
 * @param {String} title - Título del gráfico
 */
function renderUnivariateChart(labels, data, type = 'bar', title = 'Distribución de Frecuencias') {
    const canvas = document.getElementById('univariateChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');

    // Destruir la instancia previa si existe
    if (univariateChartInstance) {
        univariateChartInstance.destroy();
    }

    // Configuración específica según el tipo de gráfico
    const isBar = type === 'bar';

    univariateChartInstance = new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: data,
                backgroundColor: isBar ? chartTheme.primary : [chartTheme.primary, chartTheme.secondary, '#4a90e2', '#8ac4d0'],
                borderColor: isBar ? chartTheme.primaryBorder : '#ffffff',
                borderWidth: isBar ? 1 : 2,
                borderRadius: isBar ? 4 : 0 // Bordes redondeados solo para barras
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // Permite que el gráfico llene el contenedor padre
            plugins: {
                legend: {
                    display: !isBar, // Ocultar leyenda en barras, mostrar en donas
                    position: 'right'
                },
                title: {
                    display: true,
                    text: title,
                    font: { family: chartTheme.fontFamily, size: 16, weight: '600' },
                    color: '#1a2c3e'
                }
            },
            scales: isBar ? {
                y: {
                    beginAtZero: true,
                    grid: { color: chartTheme.gridLines }
                },
                x: {
                    grid: { display: false }
                }
            } : {} // Los gráficos de dona no usan escalas X/Y
        }
    });
}

/**
 * Renderiza el gráfico de Exploración Bivariada (Pestaña: Bivariado)
 * @param {Object} response - Configuración y datos devueltos por la API (/api/bivariate)
 * @param {String} xLabel - Nombre de la variable X
 * @param {String} yLabel - Nombre de la variable Y
 */
function renderBivariateChart(response, xLabel, yLabel) {
    const canvas = document.getElementById('bivariateChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Destruir la instancia previa si existe
    if (bivariateChartInstance) {
        bivariateChartInstance.destroy();
    }

    const chartType = response.type;

    if (chartType === 'scatter') {
        bivariateChartInstance = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: `Correlación: ${xLabel} vs ${yLabel}`,
                    data: response.data,
                    backgroundColor: chartTheme.primary,
                    borderColor: chartTheme.primaryBorder,
                    borderWidth: 1,
                    pointRadius: 6,
                    pointHoverRadius: 9,
                    pointHoverBackgroundColor: chartTheme.secondary
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(26, 44, 62, 0.9)',
                        titleFont: { family: chartTheme.fontFamily },
                        bodyFont: { family: chartTheme.fontFamily },
                        callbacks: {
                            label: (context) => ` ${xLabel}: ${context.parsed.x} | ${yLabel}: ${context.parsed.y}`
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: xLabel, font: { family: chartTheme.fontFamily, weight: 'bold' } },
                        grid: { color: chartTheme.gridLines }
                    },
                    y: {
                        title: { display: true, text: yLabel, font: { family: chartTheme.fontFamily, weight: 'bold' } },
                        grid: { color: chartTheme.gridLines }
                    }
                }
            }
        });
    } else if (chartType === 'stacked_bar') {
        bivariateChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: response.labels,
                datasets: response.datasets.map((ds, i) => {
                    const colors = [chartTheme.primary, chartTheme.secondary, '#e25a5a', '#34c38f', '#f1b44c', '#50a5f1'];
                    return {
                        label: ds.label,
                        data: ds.data,
                        backgroundColor: colors[i % colors.length]
                    };
                })
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: true, position: 'top', labels: { font: { family: chartTheme.fontFamily } } },
                    title: { display: true, text: `Distribución de ${yLabel} por ${xLabel}` }
                },
                scales: {
                    x: { stacked: true, title: { display: true, text: xLabel } },
                    y: { stacked: true, title: { display: true, text: "Frecuencia / Casos" } }
                }
            }
        });
    } else if (chartType === 'bar') {
        bivariateChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: response.labels,
                datasets: [{
                    label: response.y_label,
                    data: response.data,
                    backgroundColor: chartTheme.primary,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: true, position: 'top' },
                    title: { display: true, text: `${response.y_label} vs ${response.x_label}` }
                },
                scales: {
                    x: { title: { display: true, text: response.x_label } },
                    y: { title: { display: true, text: response.y_label }, beginAtZero: true }
                }
            }
        });
    }
}
/**
 * Renderiza el Mapa de Calor (Matriz de Correlación) usando CSS Grid
 * @param {Array} columns - Nombres de las variables (ej. ['edad', 'ingresos', 'ventas'])
 * @param {Array<Array>} matrix - Matriz NxN de correlaciones (-1 a 1)
 */
function renderHeatmap(columns, matrix) {
    const container = document.getElementById('heatmapContainer');
    if (!container) return;

    container.innerHTML = ''; // Limpiar estado previo

    // Configurar CSS Grid dinámicamente según el número de columnas
    container.style.display = 'grid';
    container.style.gridTemplateColumns = `120px repeat(${columns.length}, minmax(60px, 1fr))`;
    container.style.gap = '4px';

    // 1. Esquina superior izquierda vacía
    container.appendChild(createHeatmapCell('', 'header'));

    // 2. Cabeceras superiores (Eje X)
    columns.forEach(col => container.appendChild(createHeatmapCell(col, 'header')));

    // 3. Filas de datos
    columns.forEach((rowCol, rowIndex) => {
        // Cabecera lateral (Eje Y)
        container.appendChild(createHeatmapCell(rowCol, 'header'));

        // Celdas numéricas de la fila
        matrix[rowIndex].forEach((value, colIndex) => {
            const cell = createHeatmapCell(value.toFixed(2), 'data');
            
            // Asignar color basado en el valor de correlación
            cell.style.backgroundColor = getColorForCorrelation(value);
            
            // Tooltip nativo
            cell.title = `Correlación entre ${rowCol} y ${columns[colIndex]}: ${value.toFixed(3)}`;
            
            container.appendChild(cell);
        });
    });
}

// Función auxiliar para crear los divs
function createHeatmapCell(text, type) {
    const div = document.createElement('div');
    div.textContent = text;
    div.className = `heatmap-cell ${type}`;
    return div;
}

// Función auxiliar para mapear de -1 a 1 hacia colores RGBA
function getColorForCorrelation(value) {
    // Si la correlación es 1 (diagonal), un color neutro o el primario sólido
    if (value === 1) return 'rgba(10, 26, 36, 0.8)'; // Color oscuro para la diagonal

    const intensity = Math.abs(value);
    // Establecer un mínimo de opacidad para que los números siempre sean legibles
    const alpha = Math.max(intensity, 0.15); 

    if (value > 0) {
        // Positivo: Tonos del Azul Primario (#2c7da0 -> rgb(44, 125, 160))
        return `rgba(44, 125, 160, ${alpha})`;
    } else {
        // Negativo: Tonos Rojos/Naranjas para contraste
        return `rgba(220, 53, 69, ${alpha})`;
    }
}

// Exponer globalmente
window.renderHeatmap = renderHeatmap;
// Exponemos las funciones al entorno global para que main.js pueda usarlas
window.renderUnivariateChart = renderUnivariateChart;
window.renderBivariateChart = renderBivariateChart;