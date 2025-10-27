import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http'; // <-- ¡CRÍTICO!

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

// Importa tu módulo de funcionalidad
import { UploaderModule } from './modules/uploader/uploader.module';

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule, // <--- 1. Asegúrate de que este MÓDULO esté aquí
    UploaderModule    // <--- 2. Asegúrate de que tu módulo esté aquí
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }