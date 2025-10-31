# backend/embeddings.py
"""
轻量级文本向量化模块（基于 HashingVectorizer）
✅ 无 OOM 风险 | ✅ 内存恒定 | ✅ 无需 fit | ✅ 支持流式处理
"""

from sklearn.feature_extraction.text import HashingVectorizer
from typing import List
import gc

# 🔥 全局单例：HashingVectorizer（内存固定，无需训练）
_vectorizer = HashingVectorizer(
    n_features=1024,           # 固定维度（1KB~10MB 级文档足够）
    analyzer="word",           # 按词分割
    ngram_range=(1, 1),        # 仅 unigram（更安全，bigram 易膨胀）
    stop_words="english",      # 过滤常见词
    alternate_sign=False,      # 避免负数特征
    norm="l2"                  # 归一化，便于 cosine 相似度计算
)

# 📄 存储原始文本（用于检索后返回）
_texts = []

def build_embeddings(texts: List[str]):
    """
    哈希向量化：无需拟合，直接存储文本
    Args:
        texts: 文本块列表
    Returns:
        None（向量在 transform 时实时生成）
    """
    global _texts
    print(f"[INFO] 🔹 Received {len(texts)} chunks for indexing (HashingVectorizer)", flush=True)
    
    # 清理旧数据（可选）
    if _texts:
        print("[INFO] 🧹 Clearing previous text store...", flush=True)
    
    _texts = texts.copy()  # 保存文本用于后续检索
    print(f"[INFO] ✅ Text store updated with {len(_texts)} chunks.", flush=True)
    
    # 强制垃圾回收
    gc.collect()
    return None  # 不返回矩阵


def get_embeddings(texts: List[str]):
    """
    为查询或新文本生成哈希向量
    Returns:
        scipy.sparse matrix (n_samples, 1024)
    """
    if not _texts:
        raise RuntimeError("No documents indexed. Please upload a file first.")
    return _vectorizer.transform(texts)


def get_texts() -> List[str]:
    """获取所有已索引的文本块"""
    return _texts


def is_fitted() -> bool:
    """HashingVectorizer 无需拟合，始终可用"""
    return len(_texts) > 0


def clear_index():
    """清空索引（可选）"""
    global _texts
    _texts = []
    gc.collect()