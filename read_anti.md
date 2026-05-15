Ran command: `python scratch/test_llm_node.py`
Ran command: `python scratch/test_llm_pipeline.py 153913`

**Mới chỉ chạy batch đầu tiên thôi!** Nhìn vào code hiện tại:

```python
# Chạy batch đầu tiên
result = extractor.extract_batch(batches[0])  # ← chỉ batch 0
```

Văn bản `153913` có **756 leaf nodes → 73 batches**. Hiện tại chỉ đang test batch 1 (16 node).

Bạn có muốn tôi cập nhật `test_llm_pipeline.py` để chạy **toàn bộ tất cả batches**, gom kết quả lại và lưu ra file JSON không? Tôi sẽ thêm:
- Vòng lặp qua toàn bộ batches
- Progress log (`Batch 1/73...`)
- Lưu output ra `scratch/output_<doc_id>.json`