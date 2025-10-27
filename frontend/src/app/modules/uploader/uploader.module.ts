import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http'; // ¡Necesario para el servicio!
import { FormsModule } from '@angular/forms'; // Necesario para (ngModel) si lo usas, o para el input file.
import { UploaderComponent } from './uploader.component';
// Si estás usando rutas, también necesitarías: import { RouterModule } from '@angular/router';

@NgModule({
  declarations: [
    UploaderComponent // <--- ESTO CAUSABA EL ERROR CON STANDALONE: TRUE
  ],
  imports: [
    CommonModule,
    HttpClientModule, // Asegúrate de que esto esté aquí
    FormsModule
    // RouterModule, si aplica
  ],
  providers: [],
  exports: [
    UploaderComponent
  ]
})
export class UploaderModule { }