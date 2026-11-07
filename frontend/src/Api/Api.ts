// Third Party
import { createApiClient } from "aa-geuthur-react";

// AA Ledger
import type { paths } from "@/Api/OpenApi";

/** The API client of the app: openapi-fetch with the Django CSRF header, typed with the generated paths. */
export const apiClient = createApiClient<paths>();
