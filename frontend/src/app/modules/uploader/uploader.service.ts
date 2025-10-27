import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http'; 
import { Observable, of, delay } from 'rxjs';
// ✅ Importaciones corregidas para tipos
import { ContactRow, ValidSheet, InvalidSheet, UploadResponse, SaveResponse, StatsResponse } from './interfaces'; 

@Injectable({
  providedIn: 'root'
})
export class UploaderService {

  // Simulación de base de datos local para mantener el estado histórico
  private contactsHistory: ContactRow[] = [
    { id: 101, nombre: 'Histórico A', direccion: 'Dir H1', telefono: '111-1111', correo: 'a@hist.com' },
    { id: 102, nombre: 'Histórico B', direccion: 'Dir H2', telefono: '222-2222', correo: 'b@hist.com' },
    { id: 101, nombre: 'Histórico C', direccion: 'Dir H3', telefono: '333-3333', correo: 'c@hist.com' },
  ];

  constructor(private http: HttpClient) { 
    console.log("UploaderService initialized with HTTP simulation.");
  }

  // SIMULACIÓN 1: File Upload (for Temporary Table)
  uploadFile(file: File): Observable<UploadResponse> {
    
    // Simulated data for Temporary Table
    const simulatedData: ContactRow[] = [
      { id: 103, nombre: 'Temporal X', direccion: 'Calle TX #1', telefono: '400-4444', correo: 'tx@temp.com' },
      { id: 104, nombre: 'Temporal Y', direccion: 'Carrera TY #2', telefono: '500-5555', correo: 'ty@temp.com' },
      { id: 105, nombre: 'Temporal Z', direccion: 'Avenida TZ #3', telefono: '600-6666', correo: 'tz@temp.com' },
    ];

    const validSheets: ValidSheet[] = [
      { sheetName: 'Hoja Contactos A', rowCount: 2, data: simulatedData.slice(0, 2), isSelected: true },
      { sheetName: 'Hoja Contactos B', rowCount: 1, data: simulatedData.slice(2, 3), isSelected: true },
    ];
    
    // Invalid sheets simulation
    const invalidSheets: InvalidSheet[] = [
      { sheetName: 'Datos Sucios', reason: 'Missing required fields in 10% of rows.' }
    ];

    const response: UploadResponse = {
      filename: file.name,
      valid_sheets: validSheets,
      invalid_sheets: invalidSheets
    };

    return of(response).pipe(delay(1500)); 
  }

  // SIMULACIÓN 2: Data Saving
  saveData(data: ContactRow[]): Observable<SaveResponse> {
    
    // Add new data to history
    this.contactsHistory = [...this.contactsHistory, ...data];

    const response: SaveResponse = {
      message: `Successful save: ${data.length} records added.`,
      count: data.length
    };
    
    return of(response).pipe(delay(1000));
  }
  
  // SIMULACIÓN 3: Get Historical Contacts
  getContacts(): Observable<ContactRow[]> {
    return of([...this.contactsHistory]).pipe(delay(500)); 
  }
  
  // SIMULACIÓN 4: Get Statistics (Chart)
  getContactsStats(): Observable<StatsResponse> {
    
    let statsMap: { [key: string]: number } = {};
    this.contactsHistory.forEach(contact => {
        const idKey = `ID ${contact.id}`;
        statsMap[idKey] = (statsMap[idKey] || 0) + 1;
    });

    const labels = Object.keys(statsMap).sort();
    const data = labels.map(label => statsMap[label]);

    const response: StatsResponse = { labels, data };
    
    return of(response).pipe(delay(500));
  }
}