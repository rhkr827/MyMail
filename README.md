# MyMail
    - Mail 자동 분류 및 정리 위한 프로젝트  
#### 프로젝트 목적
    - Mail 자동 분류 및 정리 위한 프로젝트
    - Gmail 정리하다, 메일 리스트화하여 정리하는 것이 나을 것 같아 계획
#### 프로젝트 계획
##### Ver 1.0 Google Gmail Filter 생성을 위한 Python Scripts
    - 개인 Gmail에 있는 모든 메일의 보낸 사람 메일 주소를 저장 후 그룹화
    - 그룹화된 메일 주소 중 필요한 것은 Gmail Filter 생성, 필요 없는 거는 메일 오는 것을 막거나 삭제

##### Ver 2.0 Outlook으로 메일 List 생성 Python scripts
    - Office 365 구독한 김에 Outlook에 타 메일 계정 연동하여 메일 List 생성
    - Ver 1.0 Refactoring하여 기존 Gmail mail별, Domain별 List 생성 코드와 구분하여 진행
    - Python으로 domain > mail 구조로 규칙 생성 후 정리
