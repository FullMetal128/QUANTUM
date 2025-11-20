from pyqpanda3.qcloud import QCloudService
from const.constants import QUANTUM_TOKEN_API

service = QCloudService(QUANTUM_TOKEN_API)

backends = service.backends()
print(f'Квантовые компьютеры {backends}')
