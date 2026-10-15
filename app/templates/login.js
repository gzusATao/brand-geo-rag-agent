"use strict";
const password = document.getElementById("login-password");
document.getElementById("toggle-password").addEventListener("click", (event) => {
  const visible = password.type === "password";
  password.type = visible ? "text" : "password";
  event.currentTarget.textContent = visible ? "隐藏" : "显示";
  event.currentTarget.setAttribute("aria-label", visible ? "隐藏密码" : "显示密码");
  event.currentTarget.setAttribute("aria-pressed", String(visible));
});
document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.getElementById("login-submit");
  const message = document.getElementById("login-message");
  button.disabled = true;
  const label = button.querySelector(".login-button-label");
  label.textContent = "正在登录…";
  message.textContent = "";
  try {
    const response = await fetch("/api/v1/auth/login", {
      method: "POST", headers: {"Content-Type": "application/json", "X-GEO-Request": "1"},
      body: JSON.stringify({username: document.getElementById("login-username").value.trim(), password: password.value})
    });
    if (!response.ok) throw new Error((await response.json()).detail || "登录失败，请稍后重试");
    password.value = "";
    window.location.replace("/");
  } catch (error) {
    message.textContent = error instanceof TypeError ? "无法连接服务，请检查网络后重试" : error.message;
  } finally { button.disabled = false; label.textContent = "立即登录"; }
});
