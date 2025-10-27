import { Injectable } from '@angular/core';
import { HttpClient, HttpEventType } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

// Definimos la estructura de la respuesta de progreso para mejor tipado
interface UploadEvent {
  status: 'progress' | 'complete' | 'ignored' | 'error';
  message?: number;
  response?: any;
}

@Injectable({
  // providedIn: 'root' asegura que esté disponible en toda la aplicación
  providedIn: 'root' 
})
export class ApiService {
  // Asegúrate de que esta URL coincida con tu backend
  private baseUrl = 'http://localhost:8000'; 

  constructor(private http: HttpClient) { }

  uploadFile(file: File): Observable<UploadEvent> {
    const formData = new FormData();
    formData.append('excel_file', file, file.name);

    return this.http.post<any>(`${this.baseUrl}/upload_and_validate`, formData, {
      reportProgress: true, 
      observe: 'events'     
    }).pipe(
      map(event => {
        if (event.type === HttpEventType.UploadProgress) {
          // Si el total es 0 o indefinido, usamos 1 para evitar división por cero
          const progress = Math.round(100 * event.loaded / (event.total || 1));
          return { status: 'progress', message: progress };
        } else if (event.type === HttpEventType.Response) {
          return { status: 'complete', response: event.body };
        }
        return { status: 'ignored' };
      })
    );
  }
}
