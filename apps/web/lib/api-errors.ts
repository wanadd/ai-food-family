export type ApiErrorDetail = {
  code?: string;
  message?: string;
  ams_cost?: number;
  can_pay_with_ams?: boolean;
  ams_balance?: number;
};

export class ApiRequestError extends Error {
  code?: string;
  amsCost?: number;
  canPayWithAms?: boolean;
  amsBalance?: number;

  constructor(message: string, detail?: ApiErrorDetail) {
    super(message);
    this.name = "ApiRequestError";
    this.code = detail?.code;
    this.amsCost = detail?.ams_cost;
    this.canPayWithAms = detail?.can_pay_with_ams;
    this.amsBalance = detail?.ams_balance;
  }
}

export function parseApiErrorDetail(detail: unknown): ApiErrorDetail | null {
  if (!detail) return null;
  if (typeof detail === "string") {
    return { message: detail };
  }
  if (typeof detail === "object" && detail !== null && "message" in detail) {
    return detail as ApiErrorDetail;
  }
  return null;
}

export function getErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return "Что-то пошло не так";
}
