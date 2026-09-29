import React, { useRef, useState } from "react";
import api from "./api";

const MAX_SIZE_MB = 3;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

export const AvatarUpload = ({ currentAvatarUrl, userName = "User", onAvatarUpdated }) => {
  const fileInputRef = useRef(null);
  const [preview, setPreview] = useState(currentAvatarUrl || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);

    if (!ALLOWED_TYPES.includes(file.type)) {
      setError("Формат не підтримується. Виберіть PNG, JPG або WEBP.");
      return;
    }

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`Розмір файлу не повинен перевищувати ${MAX_SIZE_MB}MB.`);
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    try {
      const response = await api.post("/users/me/avatar", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setPreview(response.data.avatar_url);
      onAvatarUpdated(response.data.avatar_url);
    } catch (err) {
      setError(err.response?.data?.detail || "Не вдалося завантажити аватар.");
      setPreview(currentAvatarUrl || null);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAvatar = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.delete("/users/me/avatar");
      setPreview(null);
      onAvatarUpdated(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      setError(err.response?.data?.detail || "Помилка при видаленні аватара");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "12px" }}>
      {/* Велика кругла аватарка з ховер-ефектом */}
      <div 
        onClick={() => !loading && fileInputRef.current?.click()}
        style={{
          position: "relative",
          width: "120px",
          height: "120px",
          borderRadius: "50%",
          overflow: "hidden",
          border: "2px solid #444",
          backgroundColor: "#222",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: loading ? "not-allowed" : "pointer",
        }}
        className="avatar-container-hover"
      >
        {preview ? (
          <img src={preview} alt={userName} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <span style={{ fontSize: "36px", fontWeight: "600", color: "#888" }}>
            {userName.charAt(0).toUpperCase()}
          </span>
        )}

        {/* Напівпрозорий оверлей, який з'являється при наведенні мишки */}
        <div style={{
          position: "absolute",
          inset: 0,
          backgroundColor: "rgba(0, 0, 0, 0.6)",
          color: "#fff",
          fontSize: "12px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          opacity: 0,
          transition: "opacity 0.2s ease",
        }} className="avatar-overlay">
          {loading ? "..." : "Змінити фото"}
        </div>
      </div>

      {/* Справжній інпут повністю ховаємо через inline-стиль display: none */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept="image/png, image/jpeg, image/webp"
        style={{ display: "none" }} 
      />

      {/* Панель керування під аватаркою */}
      <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          className="secondary-button"
          style={{ padding: "4px 12px", fontSize: "12px" }}
        >
          {preview ? "Оновити" : "Обрати файл"}
        </button>

        {preview && (
          <button
            type="button"
            onClick={handleDeleteAvatar}
            disabled={loading}
            className="secondary-button"
            style={{ padding: "4px 12px", fontSize: "12px", color: "#ff4d4d", borderColor: "#ff4d4d" }}
          >
            Видалити
          </button>
        )}
      </div>

      {error && <p style={{ color: "#ff4d4d", fontSize: "12px", margin: "4px 0 0 0" }}>{error}</p>}
    </div>
  );
};
