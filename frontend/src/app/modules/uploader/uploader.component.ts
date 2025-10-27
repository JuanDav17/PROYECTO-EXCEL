import { Component, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { UploaderService } from './uploader.service';
import { HttpErrorResponse } from '@angular/common/http';
// ✅ Ruta corregida a interfaz local
import { ValidSheet, InvalidSheet, ContactRow, UploadResponse, StatsResponse } from './interfaces'; 

// Declaración global de Chart.js
declare var Chart: any; 

// ✅ SE ELIMINÓ standalone: true para funcionar con tu uploader.module.ts
@Component({
  selector: 'app-uploader',
  templateUrl: './uploader.component.html', 
  styleUrls: ['./uploader.component.scss'] 
})
export class UploaderComponent implements OnInit, AfterViewInit, OnDestroy {
  
  // Estado de la Subida y Guardado
  selectedFile: File | null = null;
  message: string | null = null;
  isSuccess: boolean = false;
  isUploading: boolean = false; 
  isSaving: boolean = false;
  
  // Datos de las Hojas (Tabla Temporal)
  validSheets: ValidSheet[] = [];
  invalidSheets: InvalidSheet[] = [];
  
  // Datos Históricos (Contactos Guardados) y Gráfico
  contacts: ContactRow[] = []; 
  chartInstance: any | null = null; 
  @ViewChild('conteoChart') chartRef!: ElementRef<HTMLCanvasElement>;

  // Propiedades Calculadas
  get hasDataToSave(): boolean {
    return this.validSheets.some(sheet => sheet.isSelected);
  }

  get totalRowsSelected(): number {
    return this.validSheets
      .filter(sheet => sheet.isSelected)
      .reduce((sum, sheet) => sum + sheet.data.length, 0);
  }

  constructor(private uploaderService: UploaderService) {}

  ngOnInit(): void {
    this.fetchContacts();
  }

  ngAfterViewInit(): void {
    // Es CRÍTICO llamar a la carga del gráfico aquí para que el elemento canvas exista
    this.fetchStatsAndRenderChart();
  }

  ngOnDestroy(): void {
    if (this.chartInstance) {
      this.chartInstance.destroy();
    }
  }

  // --- Lógica del Archivo (Tabla Temporal) ---

  onFileSelected(event: Event) {
    this.resetState();
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile = input.files[0];
      this.message = `Archivo seleccionado: ${this.selectedFile!.name}`;
      this.isSuccess = true;
    } else {
      this.selectedFile = null;
    }
  }

  toggleSheetSelection(index: number): void {
    if (index >= 0 && index < this.validSheets.length) {
      this.validSheets[index].isSelected = !this.validSheets[index].isSelected;
    }
  }

  onUpload() {
    if (!this.selectedFile) {
      this.message = 'Por favor, selecciona un archivo.';
      this.isSuccess = false;
      return;
    }
    
    this.message = `Subiendo y validando el archivo: ${this.selectedFile.name}...`;
    this.isUploading = true;
    
    this.uploaderService.uploadFile(this.selectedFile).subscribe({
      next: (response: UploadResponse) => { 
        this.isUploading = false;
        this.isSuccess = true;
        
        this.validSheets = response.valid_sheets.map((sheet: ValidSheet) => ({ ...sheet, isSelected: true })); 
        this.invalidSheets = response.invalid_sheets;
        
        this.message = `✅ Validation of "${response.filename}" complete. ${this.totalRowsSelected} records ready to save.`;
      },
      error: (err: HttpErrorResponse) => {
        this.handleError(err);
      }
    });
  }

  onSaveSelectedData() {
    if (!this.hasDataToSave) {
      this.message = 'No valid sheets selected to save.';
      this.isSuccess = false;
      return;
    }

    let dataToSave: ContactRow[] = [];
    this.validSheets
        .filter(sheet => sheet.isSelected)
        .forEach(sheet => {
            dataToSave = dataToSave.concat(sheet.data);
        });

    this.message = `Starting save of ${dataToSave.length} records to DB...`;
    this.isSaving = true;

    this.uploaderService.saveData(dataToSave).subscribe({
        next: (response) => {
            this.isSaving = false;
            this.isSuccess = true;
            this.message = `🎉 ${response.message}`;
            this.validSheets = []; 
            this.invalidSheets = [];
            
            this.fetchContacts(); 
            this.fetchStatsAndRenderChart(); 
        },
        error: (err: HttpErrorResponse) => {
            this.isSaving = false;
            this.handleError(err, 'saving data');
        }
    });
  }

  // --- Lógica de Datos Históricos (Contactos Guardados) y Gráfico ---

  fetchContacts() {
    this.uploaderService.getContacts().subscribe({
        next: (data: ContactRow[]) => {
            this.contacts = data; 
        },
        error: (err: HttpErrorResponse) => {
            console.error('Error loading historical contacts:', err);
        }
    });
  }

  fetchStatsAndRenderChart() {
    this.uploaderService.getContactsStats().subscribe({
        next: (stats: StatsResponse) => {
            if (typeof Chart !== 'undefined') {
                if (this.chartRef) { 
                    this.renderChart(stats.labels, stats.data);
                } else {
                    setTimeout(() => {
                        if (this.chartRef) {
                            this.renderChart(stats.labels, stats.data);
                        }
                    }, 100);
                }
            } else {
                console.error("Chart.js is not available. Ensure the script is loaded.");
            }
        },
        error: (err: HttpErrorResponse) => {
            console.error('Error loading statistics:', err);
        }
    });
  }

  renderChart(labels: string[], data: number[]): void {
    if (this.chartInstance) {
      this.chartInstance.destroy();
    }
    
    if (this.chartRef && this.chartRef.nativeElement) {
      this.chartInstance = new Chart(this.chartRef.nativeElement, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Total Records in History',
            data: data,
            backgroundColor: 'rgba(79, 70, 229, 0.8)',
            borderColor: 'rgb(79, 70, 229)',
            borderWidth: 1,
            borderRadius: 5,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Record Count'
              }
            }
          },
          plugins: {
            legend: {
              display: true,
              position: 'top',
            },
            title: {
              display: true,
              text: 'Analysis Chart: Count of Persisted Contacts by ID'
            }
          }
        }
      });
    }
  }

  // --- Utility Functions ---

  private resetState(): void {
    this.message = null;
    this.isSuccess = false;
    this.isUploading = false;
    this.isSaving = false;
    this.validSheets = [];
    this.invalidSheets = [];
  }

  private handleError(err: HttpErrorResponse, operation: string = 'uploading file'): void {
    this.isUploading = false;
    this.isSaving = false;
    this.isSuccess = false;
    
    let detail = `Error during ${operation}: Network or CORS failure. Code: ${err.status}`;
    
    if (err.error && err.error.detail) {
        detail = `Server Error (${err.status}) during ${operation}: ${err.error.detail}`; 
    }

    this.message = detail;
    console.error(`Full error during ${operation}:`, err);
  }
}