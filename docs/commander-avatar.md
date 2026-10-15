# 企鹅主管系统头像

当前左上角使用用户合照中前方中央的老大 Skipper 原图头像，不加西装、墨镜，不改变原版造型。与首页角色卡共用原图及 CSS 取景方式，不改动图片文件。

- 当前文件：`app/templates/assets/agents/penguin-team-reference.png`
- 取景中心：原图坐标 `(237, 147)`；显示区域 44 × 44 像素。
- 旧版原创头像已停止使用，原文件保留，未删除。

## 旧版原创头像记录

以下是之前使用内置图像生成工具制作的原创企鹅特工形象记录，不是当前显示的头像，也不是电影角色原图。

- 文件：`app/templates/assets/agents/commander-avatar.png`
- 原用途：替换工作台左上角的 G 标识，现已停用。
- 生成方式：内置 image_gen，`transparent_background=true`，原图保留透明通道。
- 本次只替换系统标识，首页另外四张角色卡的插图不在本次头像替换范围内。

## 最终生成提示词

```text
Use case: stylized-concept. Asset: system avatar for a web dashboard. Design a completely original penguin secret-agent commander mascot, not based on any existing entertainment character. A stylish adult penguin wearing a tailored black suit, white shirt, narrow tie and black sunglasses. Waist-up three-quarter side view, both flippers crossed over chest, head turned toward viewer, raised chin and a playful smug confident expression. Original distinctive design: broad curved eyebrow ridge, compact rounded orange beak, angular white cheek patches, neat swept-back feather tuft, sturdy rounded torso. High-quality stylized 3D illustration with clean simple shapes and subtle cool-blue edge lighting. Square canvas, strong legible silhouette for a small app icon, subject fills 85 percent of frame, complete head and crossed arms visible. Truly transparent background, no scenery, no words, no letters, no watermark.
```
