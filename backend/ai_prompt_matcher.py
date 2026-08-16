from __future__ import annotations

from typing import Any


class AIPromptMatcher:
    """Match a Chinese prompt to the same scene, subject, and camera skills as the reference design."""

    def __init__(self) -> None:
        self.scene_database: dict[str, dict[str, Any]] = {
            "nature": {"keywords": ["山", "海", "森林", "天空", "日出", "日落", "湖", "河", "花", "树", "草原", "瀑布", "雪", "雨", "云", "风景", "花园"], "style": "cinematic", "camera": "aerial", "mood": "peaceful", "template": "壮丽的自然景观，{prompt}，广角镜头，大气磅礴，自然光线", "icon": "🏞️", "name": "自然风光"},
            "urban": {"keywords": ["城市", "街道", "建筑", "夜景", "霓虹", "车", "人群", "大厦", "都市", "繁华", "马路"], "style": "cinematic", "camera": "tracking", "mood": "dramatic", "template": "现代都市风光，{prompt}，延时摄影，霓虹灯光，繁华景象", "icon": "🏙️", "name": "城市街景"},
            "fantasy": {"keywords": ["魔法", "龙", "城堡", "精灵", "异世界", "奇幻", "仙境", "神秘", "巫师"], "style": "anime", "camera": "orbit", "mood": "dreamy", "template": "奇幻世界，{prompt}，魔法光效，史诗感，梦幻氛围", "icon": "🐉", "name": "奇幻世界"},
            "ocean": {"keywords": ["海洋", "海底", "鱼", "珊瑚", "潜水", "海浪", "沙滩", "海边", "海豚", "鲸鱼"], "style": "cinematic", "camera": "slow_push", "mood": "peaceful", "template": "美丽的海底世界，{prompt}，清澈海水，光线穿透，海洋生物", "icon": "🌊", "name": "海洋世界"},
            "space": {"keywords": ["宇宙", "星空", "星球", "太空", "银河", "宇航员", "火箭", "星际"], "style": "cinematic", "camera": "orbit", "mood": "dreamy", "template": "浩瀚宇宙，{prompt}，星空璀璨，科幻感，史诗视角", "icon": "🌟", "name": "太空宇宙"},
            "food": {"keywords": ["食物", "美食", "料理", "烹饪", "蛋糕", "餐厅", "厨师", "甜点", "水果"], "style": "commercial", "camera": "orbit", "mood": None, "template": "美食展示，{prompt}，诱人色泽，专业美食摄影，细节丰富", "icon": "🍜", "name": "美食佳肴"},
            "product": {"keywords": ["产品", "商品", "科技", "手机", "电脑", "手表", "汽车", "广告", "品牌"], "style": "commercial", "camera": "orbit", "mood": None, "template": "高端产品展示，{prompt}，影棚灯光，商业广告级制作", "icon": "💎", "name": "产品展示"},
            "indoor": {"keywords": ["房间", "室内", "办公室", "咖啡", "家", "卧室", "客厅", "厨房", "温馨"], "style": "realistic", "camera": "slow_push", "mood": "peaceful", "template": "温馨室内场景，{prompt}，暖色调，舒适氛围，自然光", "icon": "🏠", "name": "室内场景"},
        }
        self.subject_database: dict[str, dict[str, Any]] = {
            "person": {"keywords": ["人", "女孩", "男孩", "女人", "男人", "孩子", "老人", "美女", "帅哥", "模特"], "camera": "slow_push", "mood": "dramatic", "template": "人物特写，{prompt}，情感丰富，细节清晰", "icon": "👤", "name": "人物"},
            "animal": {"keywords": ["猫", "狗", "鸟", "鱼", "兔子", "老虎", "狮子", "熊猫", "宠物", "小狗", "小猫", "猫咪", "狗狗"], "camera": "tracking", "mood": "peaceful", "template": "可爱动物，{prompt}，生动活泼，毛发细节清晰", "icon": "🐾", "name": "动物"},
        }
        self.style_map = {"cinematic": "电影级画质，浅景深，35mm胶片质感", "anime": "日系动画风格，精致细节，唯美画面", "realistic": "超写实，8K分辨率，真实纹理", "commercial": "高端商业广告，产品展示，专业制作"}
        self.camera_map = {"slow_push": "缓慢推近镜头，逐渐聚焦主体", "orbit": "360度环绕拍摄，展示全貌", "aerial": "航拍视角，俯瞰全景，壮观景象", "tracking": "跟随拍摄，保持主体在画面中心"}
        self.mood_map = {"dreamy": "梦幻氛围，柔焦效果，光斑", "dramatic": "戏剧性效果，强烈对比", "peaceful": "宁静祥和，缓慢节奏", "energetic": "充满活力，快速节奏"}

    def analyze(self, prompt: str) -> dict[str, Any]:
        analysis: dict[str, Any] = {"scene": None, "subject": None, "style": None, "camera": None, "mood": None, "detected_keywords": [], "scene_info": None, "subject_info": None}
        for scene_key, scene_data in self.scene_database.items():
            matched = [keyword for keyword in scene_data["keywords"] if keyword in prompt]
            if matched:
                analysis.update(scene=scene_key, scene_info=scene_data, style=scene_data["style"], camera=scene_data["camera"], mood=scene_data["mood"])
                analysis["detected_keywords"].extend(matched)
                break
        for subject_key, subject_data in self.subject_database.items():
            matched = [keyword for keyword in subject_data["keywords"] if keyword in prompt]
            if matched:
                analysis.update(subject=subject_key, subject_info=subject_data)
                analysis["camera"] = analysis["camera"] or subject_data["camera"]
                analysis["mood"] = analysis["mood"] or subject_data["mood"]
                analysis["detected_keywords"].extend(matched)
                break
        analysis["style"] = analysis["style"] or "cinematic"
        analysis["camera"] = analysis["camera"] or "slow_push"
        analysis["mood"] = analysis["mood"] or "peaceful"
        return analysis

    def enhance(self, prompt: str, analysis: dict[str, Any]) -> str:
        parts = []
        style_desc = self.style_map.get(analysis["style"])
        if style_desc:
            parts.append(style_desc)
        if analysis["scene"] and analysis["scene_info"]:
            parts.append(analysis["scene_info"]["template"].replace("{prompt}", prompt))
        elif analysis["subject"] and analysis["subject_info"]:
            parts.append(analysis["subject_info"]["template"].replace("{prompt}", prompt))
        else:
            parts.append(f"场景描述：{prompt}")
        camera_desc = self.camera_map.get(analysis["camera"])
        if camera_desc:
            parts.append(camera_desc)
        mood_desc = self.mood_map.get(analysis["mood"])
        if mood_desc:
            parts.append(mood_desc)
        parts.extend(["高细节，无噪点，稳定画面", "专业级制作，色彩丰富", "4K分辨率，HDR效果"])
        return "，".join(parts)

    def match_and_generate(self, prompt: str) -> dict[str, Any]:
        analysis = self.analyze(prompt)
        return {"original": prompt, "analysis": analysis, "enhanced": self.enhance(prompt, analysis)}
