document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    lucide.createIcons();

    let allRecords = []; // Store records for filtering
    let displayedCount = 10; // How many records to show
    let currentFilter = 'all'; // 'all' or 'risk'
    let currentSubFilter = 'all'; // 'all', 'high', 'medium', 'low'

    // Navigation logic
    const navLinks = document.querySelectorAll('.nav-links li');
    const pages = document.querySelectorAll('.page');

    navLinks.forEach(link => {
        link.addEventListener('mouseenter', () => {
            const pageName = link.getAttribute('data-title');
            showNavPopup(link, pageName);
        });

        link.addEventListener('mouseleave', () => {
            hideNavPopup();
        });

        link.addEventListener('click', () => {
            const pageId = link.getAttribute('data-page');
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            pages.forEach(p => {
                p.classList.remove('active');
                if (p.id === pageId) p.classList.add('active');
            });
        });
    });

    const showNavPopup = (element, text) => {
        // Remove existing popups to prevent stacking
        document.querySelectorAll('.nav-popup-feedback').forEach(p => p.remove());

        const popup = document.createElement('div');
        popup.className = 'nav-popup-feedback';
        popup.innerText = text;
        
        const rect = element.getBoundingClientRect();
        popup.style.top = `${rect.top + (rect.height / 2) - 15}px`;
        popup.style.left = `${rect.right + 15}px`;
        
        document.body.appendChild(popup);
        
        // Animate in
        requestAnimationFrame(() => {
            popup.classList.add('show');
        });
    };

    const hideNavPopup = () => {
        const popup = document.querySelector('.nav-popup-feedback');
        if (popup) {
            popup.classList.remove('show');
            setTimeout(() => popup.remove(), 200);
        }
    };

    // Tab Switching Logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const riskSubTabs = document.getElementById('risk-sub-tabs');
    const subTabBtns = document.querySelectorAll('.sub-tab-btn');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.getAttribute('data-filter');
            
            if (currentFilter === 'risk') {
                riskSubTabs.classList.remove('hidden');
                currentSubFilter = 'all'; // Default to all risk
                subTabBtns.forEach(b => b.classList.remove('active'));
                subTabBtns[0].classList.add('active'); // "All Risk"
            } else {
                riskSubTabs.classList.add('hidden');
            }

            displayedCount = 10; // Reset pagination
            renderTableWithFilters();
            
            // UI Feedback: Scroll table to top
            document.querySelector('.table-container').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        });
    });

    subTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            subTabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentSubFilter = btn.getAttribute('data-subfilter');
            renderTableWithFilters();
        });
    });

    // Charts Initialization
    let churnChart, riskChart, probChart, reasonsChart;

    const initCharts = (data = [], chartStats = null) => {
        const churnCtx = document.getElementById('churnChart').getContext('2d');
        const riskCtx = document.getElementById('riskChart').getContext('2d');

        if (churnChart) churnChart.destroy();
        if (riskChart) riskChart.destroy();
        if (probChart) probChart.destroy();
        if (reasonsChart) reasonsChart.destroy();

        const churnDist = chartStats ? chartStats.churn_dist : (
            data.length > 0 ? 
            [data.filter(d => d.Churn_Prediction === 0).length, data.filter(d => d.Churn_Prediction === 1).length] : 
            [0, 0]
        );

        const riskDist = chartStats ? chartStats.risk_dist : (
            data.length > 0 ?
            [
                data.filter(d => d.Risk_Level === 'Low Risk').length,
                data.filter(d => d.Risk_Level === 'Medium Risk').length,
                data.filter(d => d.Risk_Level === 'High Risk').length
            ] : [0, 0, 0]
        );

        let probBuckets = [0, 0, 0, 0, 0]; // 0-20, 20-40, 40-60, 60-80, 80-100
        if (chartStats) {
            probBuckets = chartStats.prob_buckets;
        } else if (data.length > 0) {
            data.forEach(d => {
                let p = d.Churn_Probability;
                if (p < 20) probBuckets[0]++;
                else if (p < 40) probBuckets[1]++;
                else if (p < 60) probBuckets[2]++;
                else if (p < 80) probBuckets[3]++;
                else probBuckets[4]++;
            });
        } else {
            probBuckets = [0, 0, 0, 0, 0];
        }

        churnChart = new Chart(churnCtx, {
            type: 'doughnut',
            data: {
                labels: ['Retained', 'Churned'],
                datasets: [{
                    data: churnDist,
                    backgroundColor: ['#10b981', '#f43f5e'],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } },
                cutout: '70%'
            }
        });

        riskChart = new Chart(riskCtx, {
            type: 'bar',
            data: {
                labels: ['Low', 'Medium', 'High'],
                datasets: [{
                    label: 'Customers',
                    data: riskDist,
                    backgroundColor: ['#10b981', '#f59e0b', '#f43f5e'],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8', autoSkip: false, maxRotation: 0 } }
                },
                layout: { padding: { left: 10, right: 25, bottom: 10, top: 10 } },
                plugins: { legend: { display: false } }
            }
        });

        const probCtx = document.getElementById('probChart').getContext('2d');
        probChart = new Chart(probCtx, {
            type: 'line',
            data: {
                labels: ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'],
                datasets: [{
                    label: 'Customers',
                    data: probBuckets,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.2)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8', autoSkip: false, maxRotation: 0 } }
                },
                layout: { padding: { left: 10, right: 25, bottom: 10, top: 10 } },
                plugins: { legend: { display: false } }
            }
        });

        // REASONS CHART LOGIC
        let reasonCounts = {};
        if (chartStats) {
            reasonCounts = Object.keys(chartStats.reason_counts).length > 0 ? chartStats.reason_counts : { "No significant risk factors": 0 };
        } else if (data.length > 0) {
            data.forEach(d => {
                if (d.Risk_Level !== 'Low Risk' && d.Possible_Reasons && d.Possible_Reasons !== 'Normal') {
                    const reasons = d.Possible_Reasons.split(', ');
                    reasons.forEach(r => {
                        reasonCounts[r] = (reasonCounts[r] || 0) + 1;
                    });
                }
            });
        } else {
            reasonCounts = { "Waiting for data...": 0 };
        }

        const sortedReasons = Object.entries(reasonCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5);
            
        const reasonLabels = sortedReasons.map(r => r[0]);
        const reasonData = sortedReasons.map(r => r[1]);

        const reasonsCtx = document.getElementById('reasonsChart').getContext('2d');
        reasonsChart = new Chart(reasonsCtx, {
            type: 'bar',
            data: {
                labels: reasonLabels,
                datasets: [{
                    label: 'Occurrences',
                    data: reasonData,
                    backgroundColor: 'rgba(244, 63, 94, 0.8)',
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y', // Horizontal bar chart
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    y: { grid: { display: false }, ticks: { color: '#94a3b8', autoSkip: false, crossAlign: 'far' } }
                },
                layout: { padding: { left: 10, right: 25, bottom: 10, top: 10 } },
                plugins: { legend: { display: false } }
            }
        });
    };

    initCharts();

    // Utility to find ID in a record
    const getCustomerID = (record) => {
        const keys = Object.keys(record);
        
        // 1. Look for exact standard ID matches first (Highest Priority)
        const exactMatches = ['customerID', 'CustomerID', 'Customer_ID', 'id', 'ID', 'cid', 'CID', 'CustID'];
        const exact = keys.find(k => exactMatches.includes(k));
        if (exact) return record[exact];

        // 2. Look for partial matches but exclude known feature keywords
        const featureKeywords = ['tfidf', 'score', 'probability', 'prob', 'rate', 'prediction', 'result'];
        const partial = keys.find(k => {
            const lowK = k.toLowerCase();
            return lowK.includes('id') && !featureKeywords.some(fk => lowK.includes(fk));
        });
        if (partial) return record[partial];

        // 3. Fallback: If "Surname" exists and looks like a numeric ID (as in some finance datasets)
        if (keys.includes('Surname') && !isNaN(record['Surname'])) return record['Surname'];

        // 4. Ultimate Fallback: Return the first column if it's not a known prediction column
        const reserved = ['Churn_Prediction', 'Churn_Probability', 'Risk_Level', 'Possible_Reasons'];
        const first = keys.find(k => !reserved.includes(k));
        return first ? record[first] : 'N/A';
    };

    // Customer Lookup Logic

    // Global Search Removed

    const renderTableWithFilters = () => {
        let filtered = [...allRecords];

        // Apply Main Tab Filter
        if (currentFilter === 'risk') {
            // Apply Sub Filter
            if (currentSubFilter === 'high') {
                filtered = filtered.filter(r => r.Risk_Level === 'High Risk');
            } else if (currentSubFilter === 'medium') {
                filtered = filtered.filter(r => r.Risk_Level === 'Medium Risk');
            } else if (currentSubFilter === 'low') {
                filtered = filtered.filter(r => r.Risk_Level === 'Low Risk');
            } else {
                // 'all' subfilter for risk means High + Medium (standard risk definition)
                filtered = filtered.filter(r => r.Risk_Level === 'High Risk' || r.Risk_Level === 'Medium Risk');
            }
        }

        renderTable(filtered);
    };

    const renderTable = (data) => {
        const tbody = document.querySelector('#customer-table tbody');
        const exportBtn = document.getElementById('export-excel-btn');
        tbody.innerHTML = '';
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-muted);">No records found.</td></tr>';
            exportBtn.classList.add('hidden');
            return;
        }

        // Show all records in the scrollable view
        data.forEach(record => {
            const id = getCustomerID(record);
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${id}</td>
                <td>${record.Churn_Probability}%</td>
                <td><span class="risk-tag risk-${record.Risk_Level.toLowerCase().replace(' ', '-')}">${record.Risk_Level}</span></td>
                <td>${record.Possible_Reasons || 'None'}</td>
                <td><button class="btn btn-ghost btn-sm" onclick="window.showCustomerDetails('${id}')">Details</button></td>
            `;
            tbody.appendChild(tr);
        });

        // Show/Hide Export button and update href
        if (data.length > 0) {
            exportBtn.classList.remove('hidden');
            let downloadParam = currentFilter;
            if (currentFilter === 'risk' && currentSubFilter !== 'all') {
                downloadParam = currentSubFilter;
            }
            exportBtn.href = `/api/download?filter_type=${downloadParam}`;
            
            // Update note about remaining rows if applicable
            const totalVal = parseInt(document.getElementById('m-total').innerText.replace(/,/g, '')) || 0;
            const existingNote = document.getElementById('table-note');
            if (totalVal > 1000) {
                existingNote.innerText = `Showing top 1,000 at-risk customers (sorted by probability). Use Export to CSV to download all ${totalVal.toLocaleString()} records.`;
            } else if (data.length > 10) {
                let typeLabel = 'All Customers';
                if (currentFilter === 'risk') {
                    if (currentSubFilter === 'high') typeLabel = 'High Risk Customers';
                    else if (currentSubFilter === 'medium') typeLabel = 'Medium Risk Customers';
                    else if (currentSubFilter === 'low') typeLabel = 'Low Risk Customers';
                    else typeLabel = 'Risk Customers';
                }
                
                existingNote.innerText = `Showing all ${data.length} ${typeLabel}. Use Export to CSV for full report download.`;
            } else {
                existingNote.innerText = '';
            }
        } else {
            exportBtn.classList.add('hidden');
        }
        
        // Re-initialize icons in table
        lucide.createIcons();
     };
 
     // Handle file processing for bulk upload
     const processBulkFile = async (file) => {
         if (!file) return;
         
         const formData = new FormData();
         formData.append('file', file);
         
         // Find the Test button
         const testBtn = document.getElementById('test-btn');
         const originalText = testBtn.innerHTML;
         testBtn.innerHTML = '<div class="loader-sm"></div> Analyzing...';
         testBtn.disabled = true;
 
         try {
             const response = await fetch('/api/bulk-predict', { method: 'POST', body: formData });
             if (!response.ok) {
                 let errMsg = 'Upload failed';
                 try {
                     const err = await response.json();
                     errMsg = err.detail || errMsg;
                 } catch (jsonErr) {
                     try {
                         const txt = await response.text();
                         if (txt.includes('<title>')) {
                             const match = txt.match(/<title>(.*?)<\/title>/);
                             errMsg = match ? match[1] : `Error ${response.status}`;
                         } else {
                             errMsg = txt.substring(0, 100) || `Error ${response.status}`;
                         }
                     } catch (txtErr) {
                         errMsg = `Error ${response.status}: ${response.statusText}`;
                     }
                 }
                 throw new Error(errMsg);
             }
             const data = await response.json();
             
             if (data.status === 'success') {
                 allRecords = data.data;
                 displayedCount = 10;
                 updateDashboard(data);
                 document.getElementById('download-report').classList.remove('hidden');
                 
                 // Show a quick success toast
                 alert('Dataset processed successfully!');
             }
         } catch (err) { 
             console.error('Bulk Upload Error:', err);
             alert('Bulk analysis failed: ' + err.message); 
         }
        finally {
            testBtn.innerHTML = originalText;
            testBtn.disabled = false;
            lucide.createIcons();
        }
    };

    let selectedFile = null;

    // Bulk Prediction via Input
    const bulkUpload = document.getElementById('bulk-upload');
    bulkUpload.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            document.getElementById('file-name-display').innerText = selectedFile.name;
            document.getElementById('test-btn').classList.remove('hidden');
            e.target.value = ''; // Reset input to allow re-uploading the same file
        }
    });

    document.getElementById('test-btn').addEventListener('click', () => {
        if (selectedFile) {
            processBulkFile(selectedFile);
        }
    });

    // Invisible Global Drag and Drop
    const dropZone = document.body;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    dropZone.addEventListener('dragover', (e) => {
        e.dataTransfer.dropEffect = 'copy'; 
    });
    
    dropZone.addEventListener('drop', (e) => {
        // Only trigger if we are on the dashboard
        const activePage = document.querySelector('.page.active');
        if (!activePage || activePage.id !== 'dashboard') return;

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            const name = file.name.toLowerCase();
            if (name.endsWith('.csv') || name.endsWith('.xlsx') || name.endsWith('.xls')) {
                selectedFile = file;
                document.getElementById('file-name-display').innerText = selectedFile.name;
                document.getElementById('test-btn').classList.remove('hidden');
            } else {
                alert('Please drop a valid .csv or .xlsx file.');
            }
        }
    });

    const updateDashboard = (data) => {
        const { summary, data: records } = data;

        document.getElementById('m-churn-rate').innerText = `${summary.churn_rate}%`;
        document.getElementById('m-high-risk').innerText = summary.high_risk_customers;
        document.getElementById('m-total').innerText = summary.total_customers;
        document.getElementById('m-accuracy').innerText = `${summary.accuracy}%`;
        
        // Update Feature Importance Drivers
        const driversSection = document.getElementById('drivers-section');
        const driversList = document.getElementById('drivers-list');
        
        let importanceData = summary.feature_importance || [];
        
        // Fallback: If model importance is missing, derive from reasons in records
        if (importanceData.length === 0 && records.length > 0) {
            const counts = {};
            records.forEach(r => {
                if (r.Possible_Reasons) {
                    r.Possible_Reasons.split(',').forEach(reason => {
                        const clean = reason.trim().replace(/High |Low |No /g, '');
                        counts[clean] = (counts[clean] || 0) + 1;
                    });
                }
            });
            importanceData = Object.entries(counts)
                .map(([feature, count]) => ({ feature, importance: count / records.length }))
                .sort((a, b) => b.importance - a.importance)
                .slice(0, 8);
        }

        importanceData = importanceData.slice(0, 5);

        if (importanceData.length > 0) {
            driversSection.classList.remove('hidden');
            
            // Normalize for percentage display: total of all shown should be a relative weight
            const totalImp = importanceData.reduce((acc, curr) => acc + curr.importance, 0);
            
            driversList.innerHTML = importanceData.map(f => {
                const percentage = ((f.importance / totalImp) * 100).toFixed(1);
                
                return `
                    <div class="driver-tag">
                        <span class="driver-name">${f.feature.replace(/_/g, ' ')}</span>
                        <span class="driver-value">${percentage}%</span>
                    </div>
                `;
            }).join('');
        } else {
            driversSection.classList.add('hidden');
        }

        initCharts(records, summary.charts);
        renderTableWithFilters();
        lucide.createIcons();
    };

    // Download Logic is now handled by native <a> tag in index.html

    window.showCustomerDetails = (searchId) => {
        searchId = searchId.toString().trim().toLowerCase();
        
        if (allRecords.length === 0) {
            alert('Please upload a dataset first before searching for a customer.');
            return;
        }

        const customer = allRecords.find(r => {
            const id = getCustomerID(r);
            return id.toString().toLowerCase() === searchId;
        });

        if (!customer) {
            alert(`Customer ID '${searchId}' not found in the uploaded dataset.`);
            return;
        }

        // Switch to predict page to show the results
        const predictLink = document.querySelector('.nav-links li[data-page="predict"]');
        if (predictLink) predictLink.click();

        const resultDiv = document.getElementById('lookup-result');
        resultDiv.classList.remove('hidden');

        // Render details grid
        const detailsGrid = document.getElementById('lookup-details-grid');
        detailsGrid.innerHTML = '';
        
        const excludeKeys = ['Churn_Prediction', 'Churn_Probability', 'Risk_Level', 'Possible_Reasons'];
        Object.keys(customer).forEach(key => {
            if (!excludeKeys.includes(key)) {
                const div = document.createElement('div');
                div.innerHTML = `
                    <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.2rem;">${key}</p>
                    <p style="font-weight: 600; color: var(--text-main); font-size: 1.1rem;">${customer[key]}</p>
                `;
                detailsGrid.appendChild(div);
            }
        });

        // Render AI Analysis
        document.getElementById('result-customer-id').innerText = searchId.toUpperCase();
        document.getElementById('result-prob').innerText = `${customer.Churn_Probability}%`;
        const probBar = document.getElementById('result-prob-bar');
        probBar.style.width = '0%';
        setTimeout(() => {
            probBar.style.width = `${customer.Churn_Probability}%`;
        }, 100);

        document.getElementById('result-badge').innerText = customer.Risk_Level;
        document.getElementById('result-badge').className = `badge risk-${customer.Risk_Level.toLowerCase().replace(' ', '-')}`;
        
        const reasonsList = document.getElementById('result-reasons');
        reasonsList.innerHTML = '';
        const hasFactors = customer.Possible_Reasons && customer.Possible_Reasons !== 'Normal';
        const reasons = hasFactors ? customer.Possible_Reasons.split(', ') : ['No significant risk factors detected'];
        
        reasons.forEach(r => {
            const li = document.createElement('li');
            li.innerText = r;
            reasonsList.appendChild(li);
        });

        // Handle Primary Factor Box
        const factorBox = document.getElementById('primary-factor-box');
        const factorText = document.getElementById('result-primary-factor');
        if (hasFactors) {
            factorBox.classList.remove('hidden');
            factorText.innerText = reasons[0]; // Set the first/most important factor
        } else {
            factorBox.classList.add('hidden');
        }
        
        // Re-initialize icons
        lucide.createIcons();
        
        setTimeout(() => {
            resultDiv.scrollIntoView({ behavior: 'smooth' });
        }, 300);
    };

    // Customer Lookup Form Logic
    const lookupForm = document.getElementById('lookup-form');
    if (lookupForm) {
        lookupForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const searchId = document.getElementById('lookup-id-input').value;
            window.showCustomerDetails(searchId);
        });
    }

    // Training Logic
    const trainUpload = document.getElementById('train-upload');
    trainUpload.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const dropZone = document.getElementById('drop-zone');
        const statusDiv = document.getElementById('training-status');
        const statusText = document.getElementById('status-text');
        const progressFill = document.getElementById('train-progress-fill');
        const progressPercent = document.getElementById('progress-percent');
        const accuracyText = document.getElementById('train-accuracy-text');
        const accuracyPath = document.getElementById('accuracy-path');

        dropZone.classList.add('hidden');
        statusDiv.classList.remove('hidden');
        
        const updateProgress = (pct, text) => {
            progressFill.style.width = `${pct}%`;
            progressPercent.innerText = `${pct}%`;
            statusText.innerText = text;
        };

        // Simulated training phases
        updateProgress(10, 'Analyzing dataset structure...');
        await new Promise(r => setTimeout(r, 1500));
        
        updateProgress(30, 'Performing feature engineering...');
        await new Promise(r => setTimeout(r, 2000));
        
        updateProgress(60, 'Training Neural Network...');
        await new Promise(r => setTimeout(r, 2500));
        
        updateProgress(90, 'Validating model accuracy...');
        await new Promise(r => setTimeout(r, 1500));

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/train', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                updateProgress(100, 'Training Complete!');
                
                // Update Accuracy Viz
                const accuracy = (result.accuracy * 100).toFixed(1);
                accuracyText.innerText = `${accuracy}%`;
                accuracyPath.setAttribute('stroke-dasharray', `${accuracy}, 100`);
                
                showToast('Model improved successfully!', 'success');
                setTimeout(() => {
                    dropZone.classList.remove('hidden');
                    statusDiv.classList.add('hidden');
                    updateProgress(0, 'Ready to train model');
                }, 4000);
            } else {
                throw new Error('Training failed');
            }
        } catch (err) {
            alert('Training failed.');
            statusDiv.classList.add('hidden');
            dropZone.classList.remove('hidden');
        }
    });
});
