import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// 1. Importa el UploaderComponent. Asegúrate que la ruta sea correcta.
import { UploaderComponent } from './modules/uploader/uploader.component'; 

const routes: Routes = [
  // 2. Define la ruta por defecto (la raíz) para que cargue el componente Uploader
  { path: '', component: UploaderComponent },
  
  // Opcional: Ruta comodín para cualquier otra URL (muestra una página de error o redirige)
  { path: '**', redirectTo: '' } 
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
