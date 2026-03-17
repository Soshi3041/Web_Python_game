window.APP_CONFIG = {
  // 例: "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod/games"
  API_BASE_URL: "YOUR_API_GATEWAY_URL",

  // 認証をまだ使わない場合は false のままでOKです。
  USE_COGNITO_AUTH: false,

  // 後で必要になったら設定します。
  COGNITO_REGION: "ap-northeast-1",
  COGNITO_USER_POOL_ID: "",
  COGNITO_APP_CLIENT_ID: "",

  // 画像URLがない場合に表示するダミー画像
  DEFAULT_IMAGE_URL:
    "https://placehold.co/800x500?text=Python+Game"
};
