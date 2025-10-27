import numpy as np
import pickle
import re
import math
import os
import json
from typing import List, Dict, Any, Literal
from dataclasses import dataclass, asdict
from collections import Counter
import tiktoken
from sentence_transformers import SentenceTransformer


@dataclass
class Chunk:
    content: str
    metadata: Dict[str, Any]
    token_count: int
    char_count: int
class VietnameseHistoryChunker:
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        min_chunk_size: int = 250,
        max_chunk_size: int = 700,
        encoding_name: str = "cl100k_base"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        try:
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except:
            print("Warning: Không thể load tokenizer, dùng ước lượng")
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return len(text) // 4
    
    def build_hierarchy_string(self, hierarchy: Dict[str, str]) -> str:
        parts = [
            hierarchy.get("chapter"), hierarchy.get("section"),
            hierarchy.get("subsection"), hierarchy.get("subsubsection")
        ]
        return " > ".join(p for p in parts if p)

    def is_special_content(self, text: str) -> bool:
        patterns = [r'\|.*\|.*\|', r'\d{1,2}/\d{1,2}/\d{4}.*\d{1,2}/\d{1,2}/\d{4}', r'Timeline|Dòng thời gian|Niên biểu']
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def split_long_section(self, content: str, hierarchy: Dict) -> List[Chunk]:
        chunks = []
        paragraphs = content.split('\n\n')
        current_chunk_content = ""
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            current_tokens = self.count_tokens(current_chunk_content)
            
            if current_tokens + para_tokens > self.max_chunk_size and current_chunk_content:
                chunks.append(Chunk(current_chunk_content.strip(), hierarchy.copy(), current_tokens, len(current_chunk_content)))
                sentences = current_chunk_content.split('.')
                overlap_text = '. '.join(sentences[-2:]) if len(sentences) > 2 else ""
                current_chunk_content = overlap_text + "\n\n" + para
            else:
                current_chunk_content += "\n\n" + para
                
        if current_chunk_content.strip():
            final_tokens = self.count_tokens(current_chunk_content)
            chunks.append(Chunk(current_chunk_content.strip(), hierarchy.copy(), final_tokens, len(current_chunk_content)))
        return chunks
    
    def chunk_markdown(self, markdown_text: str) -> List[Chunk]:
        all_lines = markdown_text.split('\n')
        chunks = []
        
        current_content_lines = []
        current_hierarchy = {"chapter": "Lời nói đầu", "section": "", "subsection": "", "subsubsection": ""}

        def create_chunk_from_buffer():
            if not current_content_lines:
                return

            content = "\n".join(current_content_lines).strip()
            if not content:
                return

            # Cập nhật đường dẫn
            hierarchy_copy = current_hierarchy.copy()
            hierarchy_copy["hierarchy_path"] = self.build_hierarchy_string(hierarchy_copy)
            
            token_count = self.count_tokens(content)

            # Nếu chunk quá lớn, chia nhỏ chunk
            if token_count > self.max_chunk_size and not self.is_special_content(content):
                sub_chunks = self.split_long_section(content, hierarchy_copy)
                chunks.extend(sub_chunks)
            else:
                chunk = Chunk(
                    content=content,
                    metadata=hierarchy_copy,
                    token_count=token_count,
                    char_count=len(content)
                )
                chunks.append(chunk)

        # quét tài liệu
        for line in all_lines:
            stripped_line = line.strip()

            # Điểm cắt chunk: Bất kỳ heading nào
            if stripped_line.startswith('#'):
                # Lưu lại chunk cũ trước khi xử lý heading mới
                create_chunk_from_buffer()
                current_content_lines = []

                # Cập nhật hierarchy dựa trên heading mới
                if stripped_line.startswith('### '):
                    current_hierarchy['subsection'] = stripped_line[4:].strip()
                    current_hierarchy['subsubsection'] = ""
                elif stripped_line.startswith('## '):
                    current_hierarchy['section'] = stripped_line[3:].strip()
                    current_hierarchy['subsection'] = "" 
                    current_hierarchy['subsubsection'] = ""
                elif stripped_line.startswith('# '):
                    current_hierarchy['chapter'] = stripped_line[2:].strip()
                    current_hierarchy['section'] = ""
                    current_hierarchy['subsection'] = ""
                    current_hierarchy['subsubsection'] = ""
            else:
                # Nếu không phải heading, thêm vào buffer content
                current_content_lines.append(line)

        create_chunk_from_buffer()

        # Post-processing: Gộp các chunk quá nhỏ
        final_chunks = self._merge_small_chunks(chunks)
        print(f"số chunk được chia: {len(final_chunks)}")
        return final_chunks

    def _merge_small_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        if not chunks: return []
        merged = []
        i = 0
        while i < len(chunks):
            current = chunks[i]
            if current.token_count < self.min_chunk_size and i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                # Merge chunk nhỏ vào chunk tiếp theo
                merged_content = current.content + "\n\n---\n\n" + next_chunk.content
                merged_token_count = self.count_tokens(merged_content)
                
                if merged_token_count < self.max_chunk_size:
                    next_chunk.content = merged_content
                    next_chunk.token_count = merged_token_count
                    next_chunk.char_count = len(merged_content)
                    # Không thêm chunk hiện tại, chỉ xử lý chunk tiếp theo đã được gộp
                    i += 1
                    continue
            
            merged.append(current)
            i += 1
        return merged
        
    def save_chunks_to_json(self, chunks: List[Chunk], filepath: str):
        print(f"lưu {len(chunks)} chunks vào json...")
        chunks_as_dicts = [asdict(chunk) for chunk in chunks]
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chunks_as_dicts, f, ensure_ascii=False, indent=2)
            print(f" lưu chunk vào '{filepath}'")
        except Exception as e:
            print(f"error: {e}")