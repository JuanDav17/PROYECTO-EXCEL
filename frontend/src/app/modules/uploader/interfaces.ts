import { Observable } from 'rxjs';

export interface ContactRow {
    id: number;
    nombre: string;
    direccion: string;
    telefono: string;
    correo: string;
}

export interface ValidSheet {
    sheetName: string;
    rowCount: number;
    data: ContactRow[];
    isSelected: boolean;
}

export interface InvalidSheet {
    sheetName: string;
    reason: string;
}

export interface UploadResponse {
    filename: string;
    valid_sheets: ValidSheet[];
    invalid_sheets: InvalidSheet[];
}

export interface SaveResponse {
    message: string;
    count: number;
}

export interface StatsResponse {
    labels: string[];
    data: number[];
}

// Interfaz para el servicio (no es estrictamente necesaria en este caso, pero es buena práctica)
export interface IUploaderService {
    uploadFile(file: File): Observable<UploadResponse>;
    saveData(data: ContactRow[]): Observable<SaveResponse>;
    getContacts(): Observable<ContactRow[]>;
    getContactsStats(): Observable<StatsResponse>;
}