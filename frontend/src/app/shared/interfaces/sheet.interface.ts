// Define la estructura de una fila de contacto (la que se guarda en DB)
export interface ContactRow {
  id: string | number;
  nombre: string;
  direccion: string | null;
  telefono: string | null;
  correo: string | null;
  // Propiedad temporal para rastrear si la fila fue seleccionada, si es necesario
  selected?: boolean; 
}

// Define la estructura de una hoja de Excel que ha sido validada como correcta
export interface ValidSheet {
  sheet_name: string;
  data: ContactRow[];
  columns: string[];
  isSelected: boolean; // Estado para la selección en el frontend
}

// Define la estructura de una hoja de Excel que ha fallado la validación
export interface InvalidSheet {
  sheet_name: string;
  columns_found: string[];
  columns_expected_normalized: string[];
  error?: string;
}

// Define la respuesta completa del endpoint /upload_and_validate/
export interface UploadResponse {
  filename: string;
  valid_sheets: ValidSheet[];
  invalid_sheets: InvalidSheet[];
}