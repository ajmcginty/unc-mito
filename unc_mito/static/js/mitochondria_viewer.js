// static/mitochondria_viewer.js
class MitochondriaViewer {
    constructor(container) {
        this.container = container;
        this.tiles = new Map();
        this.currentPage = 1;
        this.totalPages = 1;
        this.currentNeuronId = null;
        
        // Bind methods
        this.loadMitosForNeuron = this.loadMitosForNeuron.bind(this);
        this.createMitoTile = this.createMitoTile.bind(this);
        this.rotateView = this.rotateView.bind(this);
        this.openInNeuroglancer = this.openInNeuroglancer.bind(this);
        this.generateScreenshots = this.generateScreenshots.bind(this);
        this.goToPage = this.goToPage.bind(this);
        this.restartScreenshots = this.restartScreenshots.bind(this);
        
        // Add global functions
        window.loadMitosForNeuron = () => this.loadMitosForNeuron();
        window.generateScreenshots = this.generateScreenshots;
        window.restartScreenshots = () => this.restartScreenshots();
    }
    
    async loadMitosForNeuron(page = 1) {
        const neuronId = document.getElementById('neuron-id').value;
        if (!neuronId) return;
        
        try {
            console.log('Loading mitochondria for neuron:', neuronId);
            const response = await fetch(`/get_mitos_for_neuron/${neuronId}?page=${page}`);
            const data = await response.json();
            
            if (data.error) {
                console.error('Error:', data.error);
                return;
            }
            
            console.log('Received data:', data);
            
            this.currentPage = data.current_page;
            this.totalPages = data.total_pages;
            this.currentNeuronId = neuronId;
            
            // Clear container
            this.container.innerHTML = '';
            this.tiles.clear();
            
            // Create tiles
            data.mitos.forEach(mito => {
                const tile = this.createMitoTile(mito);
                this.tiles.set(mito.id, {
                    element: tile,
                    currentView: 0,
                    screenshots: mito.screenshots,
                    viewState: mito.view_state
                });
                this.container.appendChild(tile);
            });
            
            // Update pagination
            this.updatePagination();
            
            // Show generate screenshots button
            document.getElementById('generate-screenshots').style.display = 'inline-block';
            document.getElementById('screenshot-status').style.display = 'none';
            
        } catch (error) {
            console.error('Error loading mitochondria:', error);
        }
    }
    
    updatePagination() {
        const pagination = document.getElementById('pagination');
        pagination.innerHTML = '';
        
        // Add previous button
        const prevButton = document.createElement('button');
        prevButton.innerHTML = '←';
        prevButton.disabled = this.currentPage === 1;
        prevButton.onclick = () => this.goToPage(this.currentPage - 1);
        pagination.appendChild(prevButton);
        
        // Function to add page button
        const addPageButton = (pageNum) => {
            const pageButton = document.createElement('button');
            pageButton.innerHTML = pageNum;
            pageButton.classList.toggle('active', pageNum === this.currentPage);
            pageButton.onclick = () => this.goToPage(pageNum);
            pagination.appendChild(pageButton);
        };
        
        // Function to add ellipsis
        const addEllipsis = () => {
            const span = document.createElement('span');
            span.innerHTML = '...';
            span.className = 'ellipsis';
            pagination.appendChild(span);
        };
        
        // Logic for which page numbers to show
        let pagesToShow = new Set();
        pagesToShow.add(1); // Always show first page
        pagesToShow.add(this.totalPages); // Always show last page
        
        // Add current page and neighbors
        for (let i = Math.max(2, this.currentPage - 1); i <= Math.min(this.totalPages - 1, this.currentPage + 1); i++) {
            pagesToShow.add(i);
        }
        
        // Convert to array and sort
        let pageArray = Array.from(pagesToShow).sort((a, b) => a - b);
        
        // Add page buttons with ellipsis
        for (let i = 0; i < pageArray.length; i++) {
            if (i > 0 && pageArray[i] > pageArray[i-1] + 1) {
                addEllipsis();
            }
            addPageButton(pageArray[i]);
        }
        
        // Add next button
        const nextButton = document.createElement('button');
        nextButton.innerHTML = '→';
        nextButton.disabled = this.currentPage === this.totalPages;
        nextButton.onclick = () => this.goToPage(this.currentPage + 1);
        pagination.appendChild(nextButton);
        
        // Add page info
        const pageInfo = document.createElement('span');
        pageInfo.className = 'page-info';
        pageInfo.innerHTML = `Page ${this.currentPage} of ${this.totalPages}`;
        pagination.appendChild(pageInfo);
    }
    
    async goToPage(page) {
        if (page < 1 || page > this.totalPages) return;
        await this.loadMitosForNeuron(page);
    }
    
    createMitoTile(mito) {
        const tile = document.createElement('div');
        tile.className = 'mito-tile';
        tile.dataset.mitoId = mito.id;
        
        // Create the image viewer
        const viewer = document.createElement('div');
        viewer.className = 'mito-viewer';
        
        // Create placeholder div for when image fails to load
        const placeholder = document.createElement('div');
        placeholder.className = 'mito-placeholder';
        placeholder.style.backgroundColor = '#e0e0e0';
        placeholder.style.width = '100%';
        placeholder.style.height = '200px';
        placeholder.style.display = 'none';
        
        const img = document.createElement('img');
        img.src = mito.screenshots[0];
        img.onerror = () => {
            img.style.display = 'none';
            placeholder.style.display = 'block';
        };
        
        viewer.appendChild(img);
        viewer.appendChild(placeholder);
        
        // Add navigation arrows
        const prevBtn = document.createElement('button');
        prevBtn.className = 'nav-btn prev';
        prevBtn.innerHTML = '←';
        prevBtn.onclick = () => this.rotateView(mito.id, 1);  // Changed from -1 to 1
        
        const nextBtn = document.createElement('button');
        nextBtn.className = 'nav-btn next';
        nextBtn.innerHTML = '→';
        nextBtn.onclick = () => this.rotateView(mito.id, -1);  // Changed from 1 to -1
        
        // Add ID label
        const idLabel = document.createElement('div');
        idLabel.className = 'mito-id-label';
        idLabel.innerHTML = `ID: ${mito.id}`;
        
        // Add Neuroglancer button
        const ngBtn = document.createElement('button');
        ngBtn.className = 'ng-btn';
        ngBtn.innerHTML = 'View in Neuroglancer';
        ngBtn.onclick = () => this.openInNeuroglancer(mito.id, mito.view_state.neuron_id);
        
        viewer.appendChild(prevBtn);
        viewer.appendChild(nextBtn);
        viewer.appendChild(idLabel);
        tile.appendChild(viewer);
        tile.appendChild(ngBtn);
        
        return tile;
    }
    
    rotateView(mitoId, direction) {
        const tile = this.tiles.get(mitoId);
        const numViews = tile.screenshots.length;
        tile.currentView = (tile.currentView + direction + numViews) % numViews;
        
        const img = tile.element.querySelector('img');
        const placeholder = tile.element.querySelector('.mito-placeholder');
        
        img.src = tile.screenshots[tile.currentView];
        img.onerror = () => {
            img.style.display = 'none';
            placeholder.style.display = 'block';
        };
        img.onload = () => {
            img.style.display = 'block';
            placeholder.style.display = 'none';
        };
    }
    
    async openInNeuroglancer(mitoId, neuronId) {
        alert('Neuroglancer integration is currently under maintenance. Please check back later.');
    }
    
    async restartScreenshots() {
        if (!confirm('Are you sure you want to clear all screenshots? This cannot be undone.')) {
            return;
        }
        
        const statusDiv = document.getElementById('screenshot-status');
        const restartBtn = document.getElementById('restart-screenshots');
        
        try {
            statusDiv.style.display = 'block';
            statusDiv.textContent = 'Clearing screenshots...';
            restartBtn.disabled = true;
            
            const response = await fetch('/restart_screenshots', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                statusDiv.textContent = data.message;
                // Reload the current view if we have a neuron loaded
                if (this.currentNeuronId) {
                    await this.loadMitosForNeuron(this.currentPage);
                }
            } else {
                statusDiv.textContent = `Error: ${data.error}`;
            }
        } catch (error) {
            statusDiv.textContent = `Error: ${error.message}`;
        } finally {
            restartBtn.disabled = false;
        }
    }
    
    async generateScreenshots() {
        const neuronId = document.getElementById('neuron-id').value;
        if (!neuronId) return;
        
        const statusDiv = document.getElementById('screenshot-status');
        const generateBtn = document.getElementById('generate-screenshots');
        
        try {
            statusDiv.style.display = 'block';
            statusDiv.textContent = 'Generating screenshots...';
            generateBtn.disabled = true;
            
            const response = await fetch(`/generate_screenshots/${neuronId}?page=${this.currentPage}`);
            const data = await response.json();
            
            if (data.success) {
                statusDiv.textContent = data.message;
                // Reload the mitochondria to show new screenshots, staying on current page
                await this.loadMitosForNeuron(this.currentPage);
            } else {
                statusDiv.textContent = `Error: ${data.error}`;
            }
        } catch (error) {
            statusDiv.textContent = `Error: ${error.message}`;
        } finally {
            generateBtn.disabled = false;
        }
    }
}

// Initialize the viewer when the page loads
document.addEventListener('DOMContentLoaded', function() {
    window.viewer = new MitochondriaViewer(document.getElementById('mito-tiles'));
});

// Function to be called from the HTML button
function loadMitosForNeuron() {
    const neuronId = document.getElementById('neuron-id').value;
    if (neuronId) {
        window.viewer.loadMitosForNeuron(neuronId);
    }
}