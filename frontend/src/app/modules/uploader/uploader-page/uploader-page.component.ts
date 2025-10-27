import { Component } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { UploaderService } from '../uploader.service';

@Component({
  selector: 'app-uploader-page',
  templateUrl: './uploader-page.component.html',
  styleUrls: ['./uploader-page.component.scss']
})
export class UploaderPageComponent {
  uploadForm: FormGroup;
  selectedFile: File | null = null;
  uploading: boolean = false;
  uploadProgress: number = 0;

  constructor(
    private fb: FormBuilder,
    private uploaderService: UploaderService
  ) {
    this.uploadForm = this.fb.group({
      excelFile: ['', Validators.required]
    });
  }

  // 1. Maneja la selección de archivos
  onFileSelected(event: any): void {
    const file = event.target.files[0];
    // Validamos la extensión del archivo
    if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      this.selectedFile = file;
      
      // >>> CORRECCIÓN: Usamos el encadenamiento opcional '?'
      // junto al operador '!' para resolver el error TS2531 de forma segura.
      this.uploadForm.get('excelFile')!.setValue(this.selectedFile?.name);
      
    } else {
      this.selectedFile = null;
      this.uploadForm.get('excelFile')?.setValue('');
      alert('Por favor, selecciona un archivo .xlsx o .xls válido.'); 
    }
  }

  // 2. Proceso de subida
  onUpload(): void {
    if (this.selectedFile && this.uploadForm.valid) {
      this.uploading = true;

      this.uploaderService.uploadFile(this.selectedFile).subscribe({
        next: (response) => {
          this.uploading = false;
          alert('¡Archivo subido y validado con éxito!');
          console.log(response);
        },
        error: (err) => {
          this.uploading = false;
          const errorMessage = err.error?.detail || 'Error en la subida y validación del archivo.';
          alert(`Error: ${errorMessage}`);
        },
        complete: () => {
          this.uploading = false;
        }
      });
    } else {
      alert('Selecciona un archivo antes de subir.');
    }
  }
}