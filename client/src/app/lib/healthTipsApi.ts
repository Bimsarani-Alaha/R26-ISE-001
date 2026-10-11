import { requestJson } from "./apiClient";

export interface HealthTipsRequest {
  shoulder_width: number;
  hip_size: number;
  height: number;
  gender: string;
  clothing_size: string;
}

export function fetchHealthTips(
  request: HealthTipsRequest,
): Promise<{ guidance: string }> {
  return requestJson("/api/health-tips", request);
}
