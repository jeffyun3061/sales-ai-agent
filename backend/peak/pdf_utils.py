import pandas as pd


def load_csv(path: str = "data/company_data.csv") -> pd.DataFrame:
    """
    CSV 파일을 DataFrame 으로 로드한다.
    기본 컬럼: company, phone_number, industry, address
    """
    return pd.read_csv(path)


def search_companies(
    df: pd.DataFrame, keyword: str, max_results: int = 5
) -> str:
    """
    회사명·업종·주소·연락처에 대해 keyword 로 부분 일치 검색.
    max_results 개 까지 요약 문자열을 반환한다.
    """
    matches = df[
        df["company"].str.contains(keyword, case=False, na=False)
        | df["industry"].str.contains(keyword, case=False, na=False)
        | df["address"].str.contains(keyword, case=False, na=False)
        | df["phone_number"].astype(str).str.contains(keyword, na=False)
    ]

    if matches.empty:
        return "일치하는 회사를 찾을 수 없습니다."

    lines = [
        f"회사명: {r.company}, 업종: {r.industry}, 위치: {r.address}"
        for _, r in matches.head(max_results).iterrows()
    ]
    return "\n".join(lines)
