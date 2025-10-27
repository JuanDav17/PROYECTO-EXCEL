import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
// Asegúrate de que este path sea correcto según la estructura de tu módulo uploader
import { UploaderComponent } from './uploader.component'; 

const routes: Routes = [{ path: '', component: UploaderComponent }];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class UploaderRoutingModule { }