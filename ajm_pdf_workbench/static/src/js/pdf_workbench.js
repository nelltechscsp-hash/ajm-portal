/** @odoo-module **/

document.addEventListener('DOMContentLoaded', function() {
    let driverCount = 1;
    let commodityCount = 1;
    let unitCount = 1;

    // Función para imprimir/guardar como PDF usando el navegador
    const printButtons = document.querySelectorAll('.btn-print-pdf');
    printButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    });

    // Botón para adicionar chofer
    const addDriverBtn = document.getElementById('add-driver-btn');
    if (addDriverBtn) {
        addDriverBtn.addEventListener('click', function() {
            driverCount++;
            const tbody = document.getElementById('drivers-tbody');
            const newRow = document.createElement('tr');
            newRow.className = 'driver-row';
            newRow.innerHTML = `
                <td><input type="text" class="form-control" name="driver_name_${driverCount}"/></td>
                <td><input type="date" class="form-control" name="driver_dob_${driverCount}"/></td>
                <td><input type="text" class="form-control" name="driver_license_${driverCount}"/></td>
                <td><input type="text" class="form-control" name="driver_state_${driverCount}" maxlength="2" style="width: 60px;"/></td>
            `;
            tbody.appendChild(newRow);
        });
    }

    // Botón para adicionar comodidad
    const addCommodityBtn = document.getElementById('add-commodity-btn');
    if (addCommodityBtn) {
        addCommodityBtn.addEventListener('click', function() {
            commodityCount++;
            const container = document.getElementById('commodities-container');
            const newItem = document.createElement('div');
            newItem.className = 'commodity-item mb-2';
            newItem.innerHTML = `
                <textarea class="form-control" name="commodity_${commodityCount}" rows="2" placeholder="Ej: PLASTIC PRODUCTS 30%"></textarea>
            `;
            container.appendChild(newItem);
        });
    }

    // Botón para adicionar unidad
    const addUnitBtn = document.getElementById('add-unit-btn');
    if (addUnitBtn) {
        addUnitBtn.addEventListener('click', function() {
            unitCount++;
            const container = document.getElementById('units-container');
            const newItem = document.createElement('div');
            newItem.className = 'unit-item mb-2';
            newItem.innerHTML = `
                <textarea class="form-control" name="unit_${unitCount}" rows="2" placeholder="Ej: 2018 /FREIGHTLINER /SEMI /VIN: 3AKJHHDR8JSKG4321 /NO PHYSICAL DAMAGE"></textarea>
            `;
            container.appendChild(newItem);
        });
    }
});
