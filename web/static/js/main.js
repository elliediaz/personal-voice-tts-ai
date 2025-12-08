/**
 * Personal Voice TTS AI - 메인 JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initForms();
    loadServiceInfo();
});

/**
 * 탭 초기화
 */
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.dataset.tab;

            // 모든 탭 버튼에서 active 제거
            tabButtons.forEach(btn => btn.classList.remove('active'));
            // 클릭한 버튼에 active 추가
            this.classList.add('active');

            // 모든 탭 컨텐츠 숨김
            tabContents.forEach(content => content.classList.remove('active'));
            // 해당 탭 컨텐츠 표시
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

/**
 * 폼 초기화
 */
function initForms() {
    // 오디오 분석 폼
    const analyzeForm = document.getElementById('analyze-form');
    if (analyzeForm) {
        analyzeForm.addEventListener('submit', handleAnalyze);
    }

    // 텍스트 전처리 폼
    const preprocessForm = document.getElementById('preprocess-form');
    if (preprocessForm) {
        preprocessForm.addEventListener('submit', handlePreprocess);
    }
}

/**
 * 오디오 분석 처리
 */
async function handleAnalyze(event) {
    event.preventDefault();

    const form = event.target;
    const fileInput = document.getElementById('audio-file');
    const resultBox = document.getElementById('analyze-result');
    const submitBtn = form.querySelector('button[type="submit"]');

    if (!fileInput.files[0]) {
        showResult(resultBox, '파일을 선택해주세요.', 'error');
        return;
    }

    // 로딩 상태
    submitBtn.disabled = true;
    submitBtn.textContent = '분석 중...';
    form.classList.add('loading');

    try {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        const response = await fetch('/api/audio/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            const resultHtml = formatAnalysisResult(data);
            showResult(resultBox, resultHtml, 'success');
        } else {
            showResult(resultBox, data.detail || '분석 실패', 'error');
        }
    } catch (error) {
        showResult(resultBox, '서버 연결 오류: ' + error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '분석 시작';
        form.classList.remove('loading');
    }
}

/**
 * 분석 결과 포맷팅
 */
function formatAnalysisResult(data) {
    return `
        <h4>분석 결과</h4>
        <dl>
            <dt>파일명</dt><dd>${data.filename}</dd>
            <dt>샘플레이트</dt><dd>${data.sample_rate} Hz</dd>
            <dt>채널</dt><dd>${data.channels}</dd>
            <dt>길이</dt><dd>${data.duration.toFixed(2)} 초</dd>
            <dt>샘플 수</dt><dd>${data.num_samples.toLocaleString()}</dd>
            ${data.spectral_centroid ? `<dt>스펙트럼 중심</dt><dd>${data.spectral_centroid.toFixed(2)} Hz</dd>` : ''}
            ${data.rms_energy ? `<dt>RMS 에너지</dt><dd>${data.rms_energy.toFixed(6)}</dd>` : ''}
        </dl>
    `;
}

/**
 * 텍스트 전처리 처리
 */
async function handlePreprocess(event) {
    event.preventDefault();

    const form = event.target;
    const textInput = document.getElementById('input-text');
    const languageSelect = document.getElementById('language');
    const resultBox = document.getElementById('preprocess-result');
    const submitBtn = form.querySelector('button[type="submit"]');

    if (!textInput.value.trim()) {
        showResult(resultBox, '텍스트를 입력해주세요.', 'error');
        return;
    }

    // 로딩 상태
    submitBtn.disabled = true;
    submitBtn.textContent = '처리 중...';
    form.classList.add('loading');

    try {
        const formData = new FormData();
        formData.append('text', textInput.value);
        formData.append('language', languageSelect.value);

        const response = await fetch('/api/text/preprocess', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            const resultHtml = formatPreprocessResult(data);
            showResult(resultBox, resultHtml, 'success');
        } else {
            showResult(resultBox, data.detail || '전처리 실패', 'error');
        }
    } catch (error) {
        showResult(resultBox, '서버 연결 오류: ' + error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '전처리 실행';
        form.classList.remove('loading');
    }
}

/**
 * 전처리 결과 포맷팅
 */
function formatPreprocessResult(data) {
    const sentencesList = data.sentences.map(s => `<li>${s}</li>`).join('');
    return `
        <h4>전처리 결과</h4>
        <dl>
            <dt>원본</dt><dd>${data.original}</dd>
            <dt>처리됨</dt><dd>${data.processed}</dd>
            <dt>언어</dt><dd>${data.language}</dd>
        </dl>
        <h4 style="margin-top: 16px;">문장 분리</h4>
        <ul style="padding-left: 20px; margin-top: 8px;">
            ${sentencesList || '<li>문장 없음</li>'}
        </ul>
    `;
}

/**
 * 서비스 정보 로드
 */
async function loadServiceInfo() {
    const infoContent = document.getElementById('info-content');
    const algorithmsList = document.getElementById('algorithms-list');

    try {
        // 서비스 정보
        const infoResponse = await fetch('/api/info');
        if (infoResponse.ok) {
            const info = await infoResponse.json();
            infoContent.innerHTML = `
                <dl>
                    <dt>서비스명</dt><dd>${info.name}</dd>
                    <dt>버전</dt><dd>${info.version}</dd>
                    <dt>설명</dt><dd>${info.description}</dd>
                    <dt>지원 형식</dt><dd>${info.supported_formats.join(', ')}</dd>
                </dl>
                <h4 style="margin-top: 16px;">주요 기능</h4>
                <ul style="padding-left: 20px; margin-top: 8px;">
                    ${info.features.map(f => `<li>${f}</li>`).join('')}
                </ul>
            `;
        }

        // 알고리즘 목록
        const algoResponse = await fetch('/api/algorithms');
        if (algoResponse.ok) {
            const algoData = await algoResponse.json();
            algorithmsList.innerHTML = `
                <ul>
                    ${algoData.algorithms.map(a => `<li>${a}</li>`).join('')}
                </ul>
                <p style="margin-top: 8px; color: var(--text-light); font-size: 0.85rem;">
                    총 ${algoData.count}개의 알고리즘 사용 가능
                </p>
            `;
        }
    } catch (error) {
        console.error('서비스 정보 로드 실패:', error);
        infoContent.innerHTML = '<p class="error">정보를 불러올 수 없습니다.</p>';
        algorithmsList.innerHTML = '<p class="error">알고리즘 목록을 불러올 수 없습니다.</p>';
    }
}

/**
 * 결과 표시
 */
function showResult(element, content, type) {
    element.innerHTML = `<div class="${type}">${content}</div>`;
    element.classList.add('show');
}
