"""
Shared pytest fixtures for the Vietnamese Legal Knowledge Graph project.

Usage:
    Import fixtures directly in test files:
    from conftest import sample_contract_text, mock_llm
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date


# ── Sample Contract Texts ───────────────────────────────────────────────────

SAMPLE_CONTRACT_TEXT = """
HỢP ĐỒNG THUÊ VĂN PHÒNG

Số: 01/2026/HĐTV

Căn cứ Bộ luật Dân sự số 91/2015/QH13;
Căn cứ Luật Thương mại số 36/2005/QH11;

BÊN A (Bên cho thuê): CÔNG TY TNHH BẤT ĐỘNG SẢN ABC
Địa chỉ: Số 123 đường Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh
Mã số thuế: 0312345678
Đại diện: Ông Nguyễn Văn A - Chức vụ: Giám đốc
CCCD: 079087654321
Số điện thoại: 0901234567
Email: contact@abc-realestate.vn

BÊN B (Bên thuê): CÔNG TY CỔ PHẦN CÔNG NGHỆ XYZ
Địa chỉ: Tầng 5, Tòa nhà DEF, số 456 đường Lê Lợi, Quận 3, TP. Hồ Chí Minh
Mã số thuế: 0398765432
Đại diện: Bà Trần Thị B - Chức vụ: Tổng Giám đốc
CCCD: 079123456789
Số điện thoại: 0912345678
Email: admin@xyz-tech.vn

ĐIỀU 1: ĐỐI TƯỢNG HỢP ĐỒNG
Bên A đồng ý cho Bên B thuê văn phòng tại Số 123 đường Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh, diện tích 200m2, tầng 10.

ĐIỀU 2: THỜI HẠN THUÊ
Thời hạn thuê: 12 tháng, từ ngày 01/06/2026 đến ngày 31/05/2027.

ĐIỀU 3: GIÁ THUÊ VÀ THANH TOÁN
3.1 Giá thuê: 50.000.000 VNĐ/tháng (Năm mươi triệu đồng).
3.2 Phương thức thanh toán: Chuyển khoản hàng tháng.
3.3 Thời hạn thanh toán: Trước ngày 05 hàng tháng.
3.4 Tài khoản ngân hàng: Số tài khoản 1234567890123 tại Vietcombank.

ĐIỀU 4: ĐẶT CỌC
Bên B đặt cọc cho Bên A số tiền 100.000.000 VNĐ (Một trăm triệu đồng) tương đương 02 tháng tiền thuê.

ĐIỀU 5: PHẠT VI PHẠM
5.1 Nếu Bên B thanh toán chậm quá 10 ngày, phạt 0.5% số tiền chậm thanh toán mỗi ngày.
5.2 Nếu Bên B đơn phương chấm dứt hợp đồng trước thời hạn, phạt 30% giá trị hợp đồng.
5.3 Nếu Bên A đơn phương chấm dứt hợp đồng trước thời hạn, phạt 30% giá trị hợp đồng và hoàn trả tiền đặt cọc.

ĐIỀU 6: BẢO HÀNH VÀ BẢO TRÌ
Bên A chịu trách nhiệm bảo trì hệ thống điện, nước, thang máy. Bên B chịu trách nhiệm bảo trì nội thất do mình lắp đặt.

ĐIỀU 7: CHẤM DỨT HỢP ĐỒNG
7.1 Hợp đồng chấm dứt khi hết thời hạn.
7.2 Một bên có quyền đơn phương chấm dứt nếu bên kia vi phạm nghiêm trọng nghĩa vụ.
7.3 Thông báo chấm dứt trước ít nhất 30 ngày.

ĐIỀU 8: GIẢI QUYẾT TRANH CHẤP
Tranh chấp được giải quyết qua thương lượng. Nếu không thành, đưa ra Tòa án nhân dân TP. Hồ Chí Minh.

ĐIỀU 9: ĐIỀU KHOẢN CHUNG
9.1 Hợp đồng có hiệu lực từ ngày ký.
9.2 Hợp đồng lập thành 04 bản, mỗi bên giữ 02 bản.

ĐẠI DIỆN BÊN A                          ĐẠI DIỆN BÊN B
(Ký, ghi rõ họ tên)                     (Ký, ghi rõ họ tên)

Nguyễn Văn A                            Trần Thị B
"""

SAMPLE_CONTRACT_NO_PII = """
HỢP ĐỒNG DỊCH VỤ

Điều 1: Phạm vi dịch vụ
Bên A cung cấp dịch vụ tư vấn pháp lý cho Bên B.

Điều 2: Thời hạn
Thời hạn dịch vụ: 06 tháng từ ngày ký.

Điều 3: Phí dịch vụ
Phí dịch vụ: 20.000.000 VNĐ/tháng.
"""

SAMPLE_LAO_DONG_CONTRACT = """
HỢP ĐỒNG LAO ĐỘNG

Số: 02/2026/HĐLĐ

BÊN A (Người sử dụng lao động): CÔNG TY TNHH ABC
Địa chỉ: Số 100 đường Pasteur, Quận 1, TP. Hồ Chí Minh
Mã số thuế: 0311111111

BÊN B (Người lao động): Ông/Cà Bà NGUYỄN VĂN C
CCCD: 079999888777
Ngày sinh: 01/01/1990
Địa chỉ: Số 50 đường Điện Biên Phủ, Quận Bình Thạnh, TP. Hồ Chí Minh
Số điện thoại: 0933333333
Email: nguyenvanc@gmail.com

ĐIỀU 1: CHỨC DANH VÀ CÔNG VIỆC
Bên B làm vị trí Kỹ sư phần mềm, bộ phận Công nghệ thông tin.

ĐIỀU 2: THỜI HỢP ĐỒNG
Thời hạn: Không xác định thời hạn, từ ngày 01/07/2026.

ĐIỀU 3: TIỀN LƯƠNG
3.1 Lương cơ bản: 25.000.000 VNĐ/tháng.
3.2 Phụ cấp: 3.000.000 VNĐ/tháng (ăn trưa, gửi xe).
3.3 Thanh toán: Chuyển khoản ngày 25 hàng tháng.

ĐIỀU 4: THỜI GIỜ LÀM VIỆC
4.1 Thời gian: 8 giờ/ngày, từ 8h00 đến 17h00, thứ 2 đến thứ 6.
4.2 Nghỉ phép: 12 ngày/năm.

ĐIỀU 5: BẢO HIỂM
Bên A đóng BHXH, BHYT, BHTN theo quy định pháp luật.

ĐIỀU 6: CHẤM DỨT HỢP ĐỒNG
6.1 Người lao động có quyền đơn phương chấm dứt, báo trước 30 ngày.
6.2 Người sử dụng lao động có quyền chấm dứt theo quy định Bộ luật Lao động.

ĐIỀU 7: PHẠT VI PHẠM
7.1 Nếu người lao động tự ý nghỉ việc không báo trước, phạt 01 tháng lương.

ĐIỀU 8: BẢO MẬT THÔNG TIN
Người lao động không được tiết lộ thông tin mật của công ty trong và sau thời gian làm việc.
"""


# ── Sample Legal Questions ──────────────────────────────────────────────────

SAMPLE_LOOKUP_QUESTION = "Điều 17 Luật Doanh nghiệp 2020 quy định gì?"
SAMPLE_TOPIC_QUESTION = "Quy định về bảo hiểm xã hội như thế nào?"
SAMPLE_VALIDITY_QUESTION = "Luật Đất đai 2013 còn hiệu lực không?"
SAMPLE_COMPARISON_QUESTION = "So sánh Luật Doanh nghiệp 2014 và 2020"
SAMPLE_CHECKLIST_QUESTION = "Thủ tục thành lập công ty TNHH cần những gì?"
SAMPLE_NUMERIC_QUESTION = "Mức phạt vi phạm hợp đồng tối đa là bao nhiêu?"


# ── PII Test Texts ──────────────────────────────────────────────────────────

PII_CCCD_TEXT = "CCCD của ông A là 079087654321 và CMND là 123456789"
PII_MST_TEXT = "Mã số thuế công ty: 0312345678"
PII_PHONE_TEXT = "Liên hệ: 0901234567 hoặc +84 90 123 4567"
PII_EMAIL_TEXT = "Email: contact@company.vn"
PII_BANK_TEXT = "STK: 1234567890123 tại Vietcombank"
PII_ADDRESS_TEXT = "Địa chỉ: số 123 đường Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh"


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_contract_text():
    """Sample contract text with PII and known clauses."""
    return SAMPLE_CONTRACT_TEXT


@pytest.fixture
def sample_contract_no_pii():
    """Sample contract text without PII."""
    return SAMPLE_CONTRACT_NO_PII


@pytest.fixture
def sample_lao_dong_contract():
    """Sample labor contract text."""
    return SAMPLE_LAO_DONG_CONTRACT


@pytest.fixture
def sample_lookup_question():
    return SAMPLE_LOOKUP_QUESTION


@pytest.fixture
def sample_topic_question():
    return SAMPLE_TOPIC_QUESTION


@pytest.fixture
def pii_test_texts():
    return {
        "cccd": PII_CCCD_TEXT,
        "mst": PII_MST_TEXT,
        "phone": PII_PHONE_TEXT,
        "email": PII_EMAIL_TEXT,
        "bank": PII_BANK_TEXT,
        "address": PII_ADDRESS_TEXT,
    }


@pytest.fixture
def mock_llm():
    """Mock LLM client returning predefined responses."""
    from src.llm.mock_provider import MockLLMProvider
    return MockLLMProvider()
