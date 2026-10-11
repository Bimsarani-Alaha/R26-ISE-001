import { requestJson } from "./apiClient";

export interface SystemSaveRequest {
  name?: string;
  phone?: string;
  email?: string;
  age?: number;
  password?: string;
  requirements?: string;
  occasion?: string;
  gender?: string;
  colorPreference?: string;
  prediction?: object | null;
  recommendations?: object[];
  bodyMeasurements?: object | null;
  metadata?: object;
}

export function saveSystemData(
  request: SystemSaveRequest,
): Promise<{ success: boolean; message: string; id: string }> {
  return requestJson("/api/register", request);
}
