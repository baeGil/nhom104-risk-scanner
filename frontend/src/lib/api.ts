import * as realContract from "./api-contract";
import * as mockContract from "./mock-api-contract";
import * as realQa from "./api-qa";
import * as mockQa from "./mock-api-qa";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API !== "false";

export const contractApi = USE_MOCK ? mockContract : realContract;
export const qaApi = USE_MOCK ? mockQa : realQa;

export { USE_MOCK };
