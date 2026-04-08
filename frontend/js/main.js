document.addEventListener('DOMContentLoaded', () => {
    // ==========================================
    // 1. Lógica de Pestañas (Tabs)
    // ==========================================
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remover activo de todos
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            
            // Activar actual
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // ==========================================
    // 2. Lógica de Drag & Drop y Subida de Archivo
    // ==========================================
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('csvFileInput');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const uploadBtn = document.getElementById('uploadBtn');
    let selectedFile = null;

    // Abrir selector al hacer clic en cualquier parte de la zona
    dropZone.addEventListener('click', (e) => {
        if (e.target !== uploadBtn) {
            fileInput.click();
        }
    });

    // Prevenir comportamientos por defecto del navegador al arrastrar
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Añadir/quitar clase visual al arrastrar encima
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    // Capturar el archivo cuando se suelta
    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    // Capturar el archivo cuando se selecciona vía clic
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    // Lógica de validación
    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.name.endsWith('.csv')) {
                selectedFile = file;
                fileNameDisplay.textContent = `✅ Archivo listo: ${file.name}`;
                uploadBtn.disabled = false;
            } else {
                alert('⚠️ Formato inválido. Por favor, selecciona un archivo .csv');
                resetFileSelection();
            }
        }
    }

    function resetFileSelection() {
        selectedFile = null;
        fileInput.value = '';
        fileNameDisplay.textContent = '';
        uploadBtn.disabled = true;
    }

    uploadBtn.addEventListener('click', async (e) => {
        e.stopPropagation(); 
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            uploadBtn.textContent = 'Procesando Agentes (Espere)...';
            uploadBtn.disabled = true;

            const response = await fetch('http://127.0.0.1:8000/api/procesar-dataset', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            await response.json();
            
            fileNameDisplay.textContent = `🚀 ¡Pipeline finalizado!`;
            uploadBtn.textContent = 'Procesar Nuevo Dataset';
            uploadBtn.disabled = false;
            
            // Cargar KPI inmediatamente después del procesamiento si estamos en 'resumen'
            document.querySelector('[data-target="resumen"]').click();

        } catch (error) {
            console.error('Error en la conexión:', error);
            fileNameDisplay.textContent = '❌ Error al conectar con FastAPI. Revisa la consola.';
            uploadBtn.textContent = 'Reintentar';
            uploadBtn.disabled = false;
        }
    });

    const HOST = 'http://127.0.0.1:8000';

    document.querySelector('[data-target="resumen"]').addEventListener('click', async () => {
        const kpiContainer = document.getElementById('kpiContainer');
        kpiContainer.innerHTML = '<p>Cargando KPIs...</p>';
        try {
            const res = await fetch(`${HOST}/api/kpis`);
            if(!res.ok) throw new Error("Error fetching KPIs");
            const data = await res.json();
            kpiContainer.innerHTML = `
                <div class="kpi-card"><h3>Total Filas</h3><p>${data.total_filas}</p></div>
                <div class="kpi-card"><h3>Total Columnas</h3><p>${data.total_columnas}</p></div>
                <div class="kpi-card"><h3>Nulos</h3><p>${data.nulos_totales}</p></div>
                <div class="kpi-card"><h3>Provincias</h3><p>${data.num_provincias}</p></div>
            `;
            // Llenar selectores globales
            let colOptions = '<option value="">Selecciona una columna...</option>';
            data.columnas.forEach(col => colOptions += `<option value="${col}">${col}</option>`);
            document.getElementById('columnSelect').innerHTML = colOptions;
            let xyOptions = '<option value="">Selecciona...</option>';
            data.columnas.forEach(col => xyOptions += `<option value="${col}">${col}</option>`);
            document.getElementById('xSelect').innerHTML = xyOptions;
            document.getElementById('ySelect').innerHTML = xyOptions;
        } catch(e) {
            console.error(e);
            kpiContainer.innerHTML = '<p style="color:red">Error al cargar KPIs</p>';
        }
    });

    document.querySelector('[data-target="eda"]').addEventListener('click', () => {
        // Inicializar vacío o refrescar si ya hay selección
        const val = document.getElementById('columnSelect').value;
        if(val) document.getElementById('columnSelect').dispatchEvent(new Event('change'));
    });

    document.getElementById('columnSelect').addEventListener('change', async (e) => {
        const col = e.target.value;
        if (!col) return;
        try {
            const res = await fetch(`${HOST}/api/univariate/${col}`);
            const data = await res.json();
            window.renderUnivariateChart(data.labels, data.data, 'bar', `Distribución de ${col}`);
        } catch(err) { console.error(err); }
    });

    document.querySelector('[data-target="bivariado"]').addEventListener('click', async () => {
        const mapContainer = document.getElementById('heatmapContainer');
        mapContainer.innerHTML = '<p style="text-align:center;">Cargando matriz de correlación...</p>';
        try {
            const res = await fetch(`${HOST}/api/correlation`);
            const data = await res.json();
            if (window.renderHeatmap && data.columns && data.columns.length > 0) {
                window.renderHeatmap(data.columns, data.matrix);
            } else {
                mapContainer.innerHTML = '<p style="text-align:center;">No hay suficientes datos numéricos para correlación.</p>';
            }
        } catch (error) {
            console.error(error);
            mapContainer.innerHTML = '<p style="color:red; text-align:center;">Error al conectar con el servidor.</p>';
        }
    });

    document.getElementById('correlateBtn').addEventListener('click', async () => {
        const x = document.getElementById('xSelect').value;
        const y = document.getElementById('ySelect').value;
        if (!x || !y) return alert("Seleccione X y Y");
        try {
            const res = await fetch(`${HOST}/api/bivariate?col_x=${x}&col_y=${y}`);
            const data = await res.json();
            if (window.renderBivariateChart) {
                window.renderBivariateChart(data, x, y);
            }
        } catch(e) { console.error(e); }
    });

    document.querySelector('[data-target="storytelling"]').addEventListener('click', async () => {
        const sb = document.getElementById('storytellingBoard');
        sb.innerHTML = '<p>Generando insights...</p>';
        try {
            const res = await fetch(`${HOST}/api/kpis`);
            const kpi = await res.json();
            sb.innerHTML = `
                <div class="insight-card">
                    <h4>Resumen del Dataset Automático</h4>
                    <p>El dataset cargado contiene <strong>${kpi.total_filas}</strong> registros distribuidos a lo largo de <strong>${kpi.num_provincias}</strong> provincias. 
                    Después del proceso de limpieza profunda, se encontraron un total de <strong>${kpi.nulos_totales}</strong> valores nulos residuales.
                    Por favor, utiliza las pestañas de "EDA Interactiva" y "Bivariado Dinámico" para explorar a detalle la distribución de frecuencias y correlaciones entre las <strong>${kpi.total_columnas}</strong> columnas analizadas de manera cruzada.
                    </p>
                </div>
            `;
        } catch(e) {
            sb.innerHTML = '<p style="color:red">Error al generar storytelling.</p>';
        }
    });

    // Disparar click inicial para cargar los KPIs que llenan los selects
    document.querySelector('[data-target="resumen"]').click();

}); 