// This file is overwritten per environment:
//   local dev  → /quote  (nginx proxies to mock-api container)
//   GitHub Pages preview → full API Gateway URL (injected by pages.yml)
//   production (CloudFront + S3) → full API Gateway URL (injected by cdk deploy)
window.CONFIG = {
  API_ENDPOINT: "/quote",
  ENV: "local",
};
