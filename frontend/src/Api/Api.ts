// Third Party
import Cookies from "js-cookie";
import createClient from "openapi-fetch";
import type { PathsWithMethod } from "openapi-typescript-helpers";

import type { paths } from "@/Api/OpenApi";

export type GetEndpoint = PathsWithMethod<paths, "get">;

export const apiClient = createClient<paths>({
  baseUrl: "/",
  credentials: "same-origin",
});

apiClient.use({
  async onRequest({ request }) {
    const csrf = Cookies.get("csrftoken");
    if (csrf) {
      request.headers.set("X-CSRFToken", csrf);
    }
    return request;
  },
});

export const getCatApi = () => apiClient;
