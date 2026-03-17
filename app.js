console.log("app.js loaded");

const config = window.APP_CONFIG || {};
const API_BASE_URL = config.API_BASE_URL || "";
const DEFAULT_IMAGE_URL =
  config.DEFAULT_IMAGE_URL || "https://placehold.co/800x500?text=No+Image";

const state = {
  games: []
};

window.addEventListener("DOMContentLoaded", () => {
  const gameForm = document.getElementById("gameForm");
  const authorInput = document.getElementById("authorInput");
  const titleInput = document.getElementById("titleInput");
  const genreInput = document.getElementById("genreInput");
  const descriptionInput = document.getElementById("descriptionInput");
  const gameUrlInput = document.getElementById("gameUrlInput");
  const imageUrlInput = document.getElementById("imageUrlInput");
  const loadBtn = document.getElementById("loadBtn");
  const resetBtn = document.getElementById("resetBtn");
  const searchInput = document.getElementById("searchInput");
  const gameList = document.getElementById("gameList");
  const loadingMessage = document.getElementById("loadingMessage");
  const statusMessage = document.getElementById("statusMessage");

  function setStatus(message, type = "") {
    statusMessage.textContent = message;
    statusMessage.className = "status-message" + (type ? ` ${type}` : "");
  }

  function setLoading(message) {
    loadingMessage.textContent = message;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatDate(value) {
    if (!value) return "日時なし";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;

    return date.toLocaleString("ja-JP", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  function normalizeGame(raw) {
    return {
      id: raw.id || crypto.randomUUID(),
      author: raw.author || raw.userName || "名無し",
      title: raw.title || raw.gameTitle || "タイトル未設定",
      genre: raw.genre || "Other",
      description: raw.description || "説明なし",
      gameUrl: raw.gameUrl || raw.url || "#",
      imageUrl: raw.imageUrl || raw.thumbnailUrl || DEFAULT_IMAGE_URL,
      createdAt: raw.createdAt || raw.created_at || ""
    };
  }

  function getFilteredGames() {
    const keyword = searchInput.value.trim().toLowerCase();
    if (!keyword) return state.games;

    return state.games.filter((game) => {
      return [game.title, game.author, game.genre, game.description]
        .join(" ")
        .toLowerCase()
        .includes(keyword);
    });
  }

  function renderGames() {
    const games = getFilteredGames();

    if (!games.length) {
      gameList.innerHTML = `
        <div class="empty-state">
          条件に合うゲームがありません。最初の1件を投稿してみてください。
        </div>
      `;
      return;
    }

    gameList.innerHTML = games
      .map((game) => {
        return `
          <article class="game-item">
            <img
              class="game-thumb"
              src="${escapeHtml(game.imageUrl || DEFAULT_IMAGE_URL)}"
              alt="${escapeHtml(game.title)} のサムネイル"
              onerror="this.src='${DEFAULT_IMAGE_URL}'"
            />
            <div class="game-content">
              <div class="game-top">
                <h3 class="game-title">${escapeHtml(game.title)}</h3>
                <span class="genre-badge">${escapeHtml(game.genre)}</span>
              </div>
              <p class="meta">投稿者: ${escapeHtml(game.author)} / 投稿日時: ${escapeHtml(formatDate(game.createdAt))}</p>
              <p class="description">${escapeHtml(game.description)}</p>
              <div class="link-row">
                <a class="link-button" href="${escapeHtml(game.gameUrl)}" target="_blank" rel="noopener noreferrer">ゲームを開く</a>
                <a class="link-button secondary" href="${escapeHtml(game.imageUrl || DEFAULT_IMAGE_URL)}" target="_blank" rel="noopener noreferrer">画像を見る</a>
              </div>
            </div>
          </article>
        `;
      })
      .join("");
  }

  async function fetchGames() {
    if (!API_BASE_URL || API_BASE_URL === "YOUR_API_GATEWAY_URL") {
      setLoading("config.js に API Gateway のURLを設定すると一覧取得できます。今はサンプル表示です。");
      state.games = [
        {
          id: "sample-1",
          author: "Soshi",
          title: "Sample Python Jump Game",
          genre: "Action",
          description: "Pythonで作成したサンプルゲームです。実際のAPIを設定するとDynamoDBのデータを表示できます。",
          gameUrl: "https://example.com/game",
          imageUrl: DEFAULT_IMAGE_URL,
          createdAt: new Date().toISOString()
        }
      ];
      renderGames();
      return;
    }

    setLoading("ゲーム一覧を読み込み中です...");

    try {
      const response = await fetch(API_BASE_URL, {
        method: "GET",
        headers: {
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        throw new Error(`一覧取得に失敗しました: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      const items = Array.isArray(data)
        ? data
        : Array.isArray(data.items)
        ? data.items
        : [];

      state.games = items.map(normalizeGame).sort((a, b) => {
        return new Date(b.createdAt || 0) - new Date(a.createdAt || 0);
      });

      setLoading(`${state.games.length} 件のゲームを表示中です。`);
      renderGames();
    } catch (error) {
      console.error(error);
      state.games = [];
      renderGames();
      setLoading("一覧取得に失敗しました。API URL、CORS、Lambdaレスポンス形式を確認してください。");
      setStatus(error.message || "エラーが発生しました。", "error");
    }
  }

  async function submitGame(event) {
    event.preventDefault();

    const payload = {
      author: authorInput.value.trim(),
      title: titleInput.value.trim(),
      genre: genreInput.value,
      description: descriptionInput.value.trim(),
      gameUrl: gameUrlInput.value.trim(),
      imageUrl: imageUrlInput.value.trim(),
      createdAt: new Date().toISOString()
    };

    if (
      !payload.author ||
      !payload.title ||
      !payload.genre ||
      !payload.description ||
      !payload.gameUrl
    ) {
      setStatus("必須項目を入力してください。", "error");
      return;
    }

    if (!API_BASE_URL || API_BASE_URL === "YOUR_API_GATEWAY_URL") {
      setStatus("config.js に API Gateway のURLを設定してください。現在は送信できません。", "error");
      return;
    }

    setStatus("投稿中です...");

    try {
      const response = await fetch(API_BASE_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`投稿に失敗しました: ${response.status} ${response.statusText} / ${errorText}`);
      }

      setStatus("投稿が完了しました。", "success");
      gameForm.reset();
      await fetchGames();
    } catch (error) {
      console.error(error);
      setStatus(error.message || "投稿に失敗しました。", "error");
    }
  }

  gameForm.addEventListener("submit", submitGame);
  loadBtn.addEventListener("click", fetchGames);
  resetBtn.addEventListener("click", () => {
    gameForm.reset();
    setStatus("");
  });
  searchInput.addEventListener("input", renderGames);

  fetchGames();
});
