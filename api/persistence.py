#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话历史持久化存储模块
提供基于文件的对话记录保存和加载功能
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

class DialoguePersistence:
    """对话历史持久化存储类"""
    
    def __init__(self, data_dir: str = "saved_sessions"):
        """
        初始化持久化存储
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.sessions_file = os.path.join(data_dir, "sessions.json")
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"创建数据目录: {self.data_dir}")
    
    def _load_sessions(self) -> Dict:
        """加载所有会话数据"""
        if not os.path.exists(self.sessions_file):
            return {}
        
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载会话文件失败: {e}")
            return {}
    
    def _save_sessions(self, sessions: Dict):
        """保存所有会话数据"""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存会话文件失败: {e}")
            raise
    
    def create_session(self, user_name: str = "用户", stage: str = "M1") -> str:
        """
        创建新的对话会话
        
        Args:
            user_name: 用户名称
            stage: 对话阶段
            
        Returns:
            会话ID
        """
        session_id = str(uuid.uuid4())
        sessions = self._load_sessions()
        
        sessions[session_id] = {
            "session_id": session_id,
            "user_name": user_name,
            "stage": stage,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "dialogue_states": {},
            "active_stage": stage,
            "history": []
        }
        
        self._save_sessions(sessions)
        print(f"创建新会话: {session_id}")
        return session_id
    
    def save_session_state(self, session_id: str, dialogue_states: Dict, 
                          active_stage: str, history: List[Dict]):
        """
        保存会话状态
        
        Args:
            session_id: 会话ID
            dialogue_states: 对话状态
            active_stage: 当前活跃阶段
            history: 对话历史
        """
        sessions = self._load_sessions()
        
        if session_id not in sessions:
            print(f"会话 {session_id} 不存在，创建新会话")
            sessions[session_id] = {
                "session_id": session_id,
                "user_name": "用户",
                "stage": active_stage,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "dialogue_states": {},
                "active_stage": active_stage,
                "history": []
            }
        
        sessions[session_id].update({
            "dialogue_states": dialogue_states,
            "active_stage": active_stage,
            "history": history,
            "last_updated": datetime.now().isoformat()
        })
        
        self._save_sessions(sessions)
        print(f"保存会话状态: {session_id}")
    
    def load_session_state(self, session_id: str) -> Optional[Dict]:
        """
        加载会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话状态字典，如果不存在则返回None
        """
        sessions = self._load_sessions()
        
        if session_id not in sessions:
            print(f"会话 {session_id} 不存在")
            return None
        
        session_data = sessions[session_id]
        print(f"加载会话状态: {session_id}")
        
        return {
            "dialogue_states": session_data.get("dialogue_states", {}),
            "active_stage": session_data.get("active_stage", "M1"),
            "history": session_data.get("history", []),
            "user_name": session_data.get("user_name", "用户"),
            "created_at": session_data.get("created_at"),
            "last_updated": session_data.get("last_updated")
        }
    
    def get_all_sessions(self) -> List[Dict]:
        """
        获取所有会话列表
        
        Returns:
            会话列表
        """
        sessions = self._load_sessions()
        
        session_list = []
        for session_id, session_data in sessions.items():
            session_list.append({
                "session_id": session_id,
                "user_name": session_data.get("user_name", "用户"),
                "stage": session_data.get("stage", "M1"),
                "created_at": session_data.get("created_at"),
                "last_updated": session_data.get("last_updated"),
                "history_count": len(session_data.get("history", []))
            })
        
        # 按最后更新时间排序
        session_list.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        return session_list
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        sessions = self._load_sessions()
        
        if session_id not in sessions:
            print(f"会话 {session_id} 不存在")
            return False
        
        del sessions[session_id]
        self._save_sessions(sessions)
        print(f"删除会话: {session_id}")
        return True
    
    def export_session(self, session_id: str, export_file: str = None) -> str:
        """
        导出会话到文件
        
        Args:
            session_id: 会话ID
            export_file: 导出文件路径，如果为None则自动生成
            
        Returns:
            导出文件路径
        """
        session_data = self.load_session_state(session_id)
        if not session_data:
            raise ValueError(f"会话 {session_id} 不存在")
        
        if not export_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = os.path.join(self.data_dir, f"session_{session_id}_{timestamp}.json")
        
        export_data = {
            "session_id": session_id,
            "exported_at": datetime.now().isoformat(),
            "session_data": session_data
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"导出会话到: {export_file}")
        return export_file
