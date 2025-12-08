import numpy as np
from sklearn.linear_model import LogisticRegression

class SimplePredictor:
    def __init__(self):
        # 로지스틱 회귀 모델 초기화 (기본 설정)
        self.model = LogisticRegression()

    def train(self, features: list, labels: list):
        """
        데이터 학습
        :param features: [[팀A공격력, 팀B수비력, ...], ...]
        :param labels: [0(패), 1(승), ...]
        """
        self.model.fit(features, labels)

    def predict(self, match_data: list) -> float:
        """
        단일 경기 승리 확률 예측 (0.0 ~ 1.0)
        """
        # predict_proba 결과: [[패배확률, 승리확률]]
        return self.model.predict_proba([match_data])[0][1]

if __name__ == "__main__":
    # 1. 더미 데이터 준비 (예시: [홈팀능력치, 원정팀능력치, 상대전적승률])
    # 실제로는 DB에서 가져온 데이터를 가공해서 넣어야 함
    X_train = np.array([
        [80, 70, 0.6], [90, 60, 0.8], [50, 85, 0.1], [70, 72, 0.4],
        [88, 85, 0.5], [60, 95, 0.0], [75, 60, 0.7], [65, 80, 0.3]
    ])
    # 1: 홈팀 승리, 0: 홈팀 패배/무승부
    y_train = np.array([1, 1, 0, 0, 1, 0, 1, 0])

    # 2. 모델 학습
    predictor = SimplePredictor()
    predictor.train(X_train, y_train)

    # 3. 새로운 경기 예측 테스트
    # 상황: 홈팀 능력치 82, 원정팀 능력치 75, 상대전적 승률 0.55
    new_match_data = [82, 75, 0.55]
    
    win_prob = predictor.predict(new_match_data)

    print(f"입력 데이터: {new_match_data}")
    print(f"홈팀 승리 예측 확률: {win_prob:.4f} ({win_prob * 100:.2f}%)")
