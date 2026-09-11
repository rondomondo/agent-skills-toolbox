// Fetches config JSON with retries and cache busting. onSuccess/validateConfig are wired up
// but not currently used — keeping them for when I get round to proper validation.
const loadConfig = async ({
    url = 'config/default.json',
    retries = 3,
    retryDelay = 1000,
    onAttempt = null,
    onSuccess = null,
    validateConfig = false,
    headers = {},
    credentials = 'same-origin',
} = {}) => {
    let lastError;

    for (let attempt = 0; attempt < retries; attempt++) {
        try {
            const cacheBuster = `_t=${Date.now()}`;
            const urlWithCache = url.includes('?') ? `${url}&${cacheBuster}` : `${url}?${cacheBuster}`;

            const response = await fetch(urlWithCache, {
                method: 'GET',
                headers: {
                    Accept: 'application/json',
                    'Cache-Control': 'no-cache',
                    ...headers,
                },
                credentials,
            });

            if (!response.ok) {
                // 4xx errors won't recover on retry
                if (response.status >= 400 && response.status < 500) {
                    const FALLBACK_URL = 'library/themes.json';
                    if (url !== FALLBACK_URL) {
                        console.warn(`Config not found [${response.status}] ${url} -- falling back to ${FALLBACK_URL}`);
                        return loadConfig({
                            url: FALLBACK_URL,
                            retries,
                            retryDelay,
                            onAttempt,
                            onSuccess,
                            validateConfig,
                            headers,
                            credentials,
                        });
                    }
                    console.warn(`Config not found [${response.status}] ${url} -- no further fallback`);
                    return { config_url: url, success: false, status: response.status, config: null };
                }
                throw new Error(`HTTP error! status: ${response.status} url: ${url}`);
            }

            const config = await response.json();
            const successObject = { config_url: url, success: true, attempt: attempt + 1, config };

            // onSuccess hook — not wired yet, falls through to plain return for now
            if (onSuccess) {
                return await onSuccess(successObject);
            }
            return successObject;
        } catch (error) {
            lastError = error;
            console.warn(`Attempt ${attempt + 1} [${url}] failed:`, error.message);

            if (onAttempt) {
                (async () => {
                    await onAttempt({ config_url: url, success: false, attempt: attempt + 1, error });
                })();
            }

            if (attempt < retries - 1) {
                await new Promise((resolve) => setTimeout(resolve, retryDelay));
            }
        }
    }

    console.warn(`Config load failed after ${retries} attempts [${url}]:`, lastError?.message);
    return { config_url: url, success: false, config: null };
};

const getRGBA = (color, opacity) => {
    const colorMap = {
        blue: [0, 0, 255],
        green: [0, 128, 0],
        indigo: [75, 0, 130],
        orange: [255, 165, 0],
        purple: [128, 0, 128],
        red: [255, 0, 0],
        teal: [0, 128, 128],
        yellow: [255, 255, 0],
    };

    if (!colorMap[color.toLowerCase()]) {
        return 'Invalid color';
    }

    const [r, g, b] = colorMap[color.toLowerCase()];
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
};

let DEFAULT_GAMES = {
    metadata: {
        generated_at: '2024-12-01T15:53:15.907124',
        source: 'https://redis.io/glossary/acid-transactions/',
        suggested_name: 'acid_transactions_concepts.json',
    },
    game_sets: [
        {
            theme: 'ACID Properties',
            game_set_id: 'default_acid_properties',
            group_sets: [
                [
                    {
                        words: ['Atomicity', 'Consistency', 'Isolation', 'Durability'],
                        category: 'ACID Characteristics',
                        color: 'red',
                        url: 'https://redis.io/glossary/acid-transactions/#understanding-acid-transactions',
                        description: 'The four key properties of an ACID transaction',
                        skill_level: 'Beginner',
                        additional_sources: [
                            'https://en.wikipedia.org/wiki/ACID',
                            'https://www.ibm.com/docs/en/cics-ts/5.4?topic=processing-acid-properties-transactions',
                        ],
                        theme: 'ACID Properties',
                        group_item_id: 'default_acid_char',
                        group_set_id: 'default_acid_gs1',
                    },
                    {
                        words: ['Begin', 'Execute', 'Commit', 'Rollback'],
                        category: 'Transaction Stages',
                        color: 'green',
                        url: 'https://redis.io/glossary/acid-transactions/#how-do-acid-transactions-work',
                        description: 'The common steps databases use to implement ACID transactions',
                        skill_level: 'Intermediate',
                        additional_sources: [
                            'https://www.geeksforgeeks.org/acid-properties-in-dbms/',
                            'https://docs.oracle.com/cd/B19306_01/server.102/b14220/transact.htm',
                        ],
                        theme: 'ACID Properties',
                        group_item_id: 'default_acid_stages',
                        group_set_id: 'default_acid_gs1',
                    },
                    {
                        words: ['Banking', 'Healthcare', 'E-commerce', 'Inventory'],
                        category: 'Industries Using ACID',
                        color: 'blue',
                        url: 'https://redis.io/glossary/acid-transactions/#acid-transactions-use-cases',
                        description: 'Examples of industries that commonly use ACID transactions',
                        skill_level: 'Beginner',
                        additional_sources: [
                            'https://www.baeldung.com/cs/transactions-intro',
                            'https://fauna.com/blog/what-is-acid-compliance-atomicity-consistency-isolation',
                        ],
                        theme: 'ACID Properties',
                        group_item_id: 'default_acid_industries',
                        group_set_id: 'default_acid_gs1',
                    },
                    {
                        words: ['BASE', 'CAP', 'NoSQL', 'Eventual Consistency'],
                        category: 'Alternative Models',
                        color: 'yellow',
                        url: 'https://redis.io/glossary/acid-transactions/#alternatives-to-acid-transactions',
                        description: 'Other transaction models and theorems besides ACID',
                        skill_level: 'Advanced',
                        additional_sources: [
                            'https://en.wikipedia.org/wiki/Eventual_consistency',
                            'https://www.bmc.com/blogs/cap-theorem/',
                            'https://neo4j.com/blog/acid-vs-base-consistency-models-explained/',
                        ],
                        theme: 'ACID Properties',
                        group_item_id: 'default_acid_alts',
                        group_set_id: 'default_acid_gs1',
                    },
                ],
            ],
        },
    ],
};

// Overriding the sample data above — runtime games come from localStorage or remote config
DEFAULT_GAMES = {};
const DEFAULT_GAMES_SET_COUNT = 0;

// ddCOLORS and DEFAULT_GAMES_ENHANCED kept around, might need them later
const ddCOLORS = ['blue', 'green', 'indigo', 'orange', 'purple', 'red', 'teal', 'yellow'];
let DEFAULT_GAMES_ENHANCED = DEFAULT_GAMES;

const COLORS = ['red', 'yellow', 'green', 'blue', 'purple', 'teal', 'orange', 'indigo'];

const DEFAULT_HINTS = 4;

const DEFAULT_LIVES = 4;

const AUTO_SOLVE_WORD_DELAY = 500;

const AUTO_SOLVE_SUBMIT_DELAY = 3000;

const limitList = (list, limit = 4) => list.slice(0, limit);

const shuffleAndTake = (list, x = 4) => {
    return [...list].sort(() => Math.random() - 0.5).slice(0, x);
};

const mergeObjects = (obj1, obj2) => {
    // Create a shallow copy of the first object to avoid mutating it
    return {
        ...obj1,
        ...obj2,
    };
};

const validateGame = (games) => {
    if (!games?.game_sets) {
        return runValidateGame(games);
    }
    return runValidateGame(games.game_sets);
};

// validateGameNew — keeping this around, it adds the empty-object check
// which validateGame doesn't do. Might consolidate these two at some point.
var validateGameNew = (games) => {
    if (games && Object.keys(games).length === 0) {
        return false;
    }
    if (!games?.game_sets) {
        return runValidateGame(games);
    }
    return runValidateGame(games.game_sets);
};

const runValidateGame = (gameData) => {
    let modified = false;

    // Handle string input — file upload or drag-drop gives us a raw string
    if (typeof gameData === 'string') {
        try {
            gameData = JSON.parse(gameData);
        } catch (e) {
            return 'Invalid JSON format';
        }
    }

    if (!Array.isArray(gameData)) {
        gameData = [gameData];
    }

    for (let game of gameData) {
        for (let group of game.group_sets) {
            if (!group || !Array.isArray(group)) {
                return 'Each group must be an array';
            }
            if (group.length !== 4) {
                return 'Each group must have exactly 4 elements';
            }

            for (let group_item of group) {
                if (!group_item.words || !group_item.category || !group_item.color) {
                    return 'Each group_item must have words, category, and color';
                }
                // words can have more than 4 — we just need at least 4 to play
                if (!Array.isArray(group_item.words) || group_item.words.length < 4) {
                    return 'Each group_item must have at least 4 words';
                }
                if (!group_item.category.trim()) {
                    return 'All categories must be filled';
                }
                if (group_item.words.some((word) => !word || !word.trim())) {
                    return 'All words must be filled';
                }
                if (!COLORS.includes(group_item.color.toLowerCase())) {
                    return `Invalid color. Must be ${COLORS}`;
                }
                group_item.color = group_item.color.toLowerCase();
            }

            // Auto-fix duplicate words rather than rejecting outright — append a suffix to dupes
            const allWords = group.flatMap((group_item) => group_item.words);
            const wordDuplicates = findDuplicates(allWords);
            if (wordDuplicates.length !== 0) {
                modified = true;
                console.log(`duplicate words found, auto-fixing: ${wordDuplicates}`);
                const normalizedWords = normalizeWordList(allWords);
                group = distributeWords(group, normalizedWords);
            }
        }
    }

    // Persist the fixed-up version back to localStorage if we changed anything
    if (modified === true) {
        let lsConfig = JSON.parse(localStorage.getItem('DEFAULT_GAMES'));
        if (lsConfig !== null) {
            lsConfig.game_sets = gameData;
            localStorage.setItem('DEFAULT_GAMES', JSON.stringify(lsConfig));
        }
    }

    return true;
};

// Not currently called — keeping it around in case I need word-diff diagnostics later
const getWordDifference = (iter1, iter2, expected_length = 16, fix = true) => {
    const list1 = [...iter1];
    const list2 = [...iter2];
    const list1Lower = list1.map((word) => word.toLowerCase());
    const list2Lower = list2.map((word) => word.toLowerCase());

    if (new Set(list1Lower).size === expected_length && new Set(list2Lower).size === expected_length) {
        return [];
    }

    const diffList = list1Lower.filter((word) => !list2Lower.includes(word));
    const list1_duplicates = findDuplicates(list1);
    const list2_duplicates = findDuplicates(list2);
    console.log(`diffList: ${diffList}  dups: ${list1_duplicates} ${list2_duplicates}`);
    return [];
};

const normalizeWordList = (words, expected_length = null) => {
    // Early validation if expected_length is provided
    if (expected_length && words.length !== expected_length) {
        throw new Error(`List must contain exactly ${expected_length} words`);
    }

    const wordCount = new Map();

    return words.map((word) => {
        const lowerWord = word.toLowerCase();

        // Get current count for this word
        const count = wordCount.get(lowerWord) || 0;
        wordCount.set(lowerWord, count + 1);

        // First occurrence stays original, others get numbered
        if (count > 0) {
            return `${word}_${count}`;
        }
        return word;
    });
};

// Not currently called — keeping for potential use
const normalizeColors = (colors, expected_length = null) => {
    if (expected_length && colors.length !== expected_length) {
        throw new Error(`List must contain exactly ${expected_length} colors`);
    }
    return colors.map((color) => color.toLowerCase());
};

// Helper function if you need to find duplicates separately
const findDuplicates = (words) => {
    const seen = new Set();
    const duplicates = new Set();

    words.forEach((word) => {
        const lowerWord = word.toLowerCase();
        if (seen.has(lowerWord)) {
            duplicates.add(word);
        }
        seen.add(lowerWord);
    });

    return [...duplicates];
};

const distributeWords = (group, normalizedWords) => {
    if (normalizedWords.length !== 16) {
        throw new Error('Normalized words array must contain exactly 16 words');
    }

    let wordIndex = 0;
    for (let group_item of group) {
        if (!group_item.words || !group_item.category || !group_item.color) {
            return 'Each group_item must have words, category, and color';
        }

        // Take next 4 words from normalized array
        group_item.words = normalizedWords.slice(wordIndex, wordIndex + 4);
        wordIndex += 4;
    }
    return group;
};

const mergeObjectArrays = (originalArray, newArray) => {
    // Create a map of the original array objects by group_item_id for easy lookup
    const originalMap = new Map(originalArray.map((item) => [item.group_item_id, item]));

    return newArray.map((newItem) => {
        // Find matching original object by group_item_id
        const originalItem = originalMap.get(newItem.group_item_id);

        if (originalItem) {
            // If there's a matching item, merge while preserving nested structures
            return {
                ...originalItem,
                ...newItem,
                words: newItem.words || originalItem.words,
                theme: originalItem.theme || newItem.groupThemeName,
                description: newItem.description ?? originalItem.description,
                skill_level: newItem.skill_level || originalItem.skill_level,
                url: newItem.url ?? originalItem.url,
                additional_sources: newItem.additional_sources?.length
                    ? newItem.additional_sources
                    : originalItem.additional_sources || [],
            };
        }

        // If no matching item exists, add the new item with default structures
        return {
            ...newItem,
            theme: newItem.groupThemeName,
            additional_sources: [],
            url: '',
            description: '',
            skill_level: 'Intermediate', // Default value
        };
    });
};

const virtualShiftKeyPressed = () => {
    return document.querySelector('.shift-btn').disabled === true;
};

const virtualShiftKeyReset = () => {
    return (document.querySelector('.shift-btn').disabled = false);
};

const createDblClick = (element, callback, timeout = 400) => {
    let clicks = 0;
    let timeoutId = null;

    ['dblclick', 'touchend'].forEach((eventType) => {
        element.addEventListener(eventType, (e) => {
            clicks++;
            console.log('event:', eventType, 'clicks:', clicks, 'e', e);

            if (clicks === 1) {
                timeoutId = setTimeout(() => {
                    // If we get here, it was a single click/tap
                    clicks = 0;
                    // For touchend, simulate a click event
                    if (eventType === 'touchend') {
                        makeCustomDaveClick(e.target);

                        // const clickEvent = new MouseEvent('click', {
                        //     bubbles: true,
                        //     cancelable: true,
                        //     view: window,
                        // });
                        // e.target.dispatchEvent(clickEvent);
                    }
                }, timeout);
            } else if (clicks === 2) {
                console.log('event:', eventType, 'clicks:', clicks, 'e', e);
                e.preventDefault();
                //e.stopPropagation();
                clearTimeout(timeoutId);
                clicks = 0;
                timeoutId = null;
                callback(e);
            }
        });
    });
};

// Currently a passthrough — the group-flattening/sampling logic below the early return
// is dead but kept intentionally. Might revisit when I add multi-set mixing.
const transformJson = (inputJson, maxEntries = 4) => {
    return inputJson;

    if (!inputJson?.game_sets) {
        let gameData = JSON.parse(JSON.stringify(inputJson));
        if (!Array.isArray(gameData)) {
            gameData = [gameData];
        }
        return gameData;
    }

    let inputJsonClone = JSON.parse(JSON.stringify(inputJson));
    return inputJsonClone;

    const transformedGroups = inputJsonClone.game_sets.reduce((acc, groupSet) => {
        return acc.concat(groupSet.groups);
    }, []);

    if (transformedGroups.length > maxEntries) {
        const selectedGroups = [];
        for (let i = 0; i < maxEntries; i++) {
            const randomIndex = Math.floor(Math.random() * transformedGroups.length);
            selectedGroups.push(transformedGroups.splice(randomIndex, 1)[0]);
        }
        return [{ groups: selectedGroups }];
    }

    return [{ groups: transformedGroups }];
};

// Stable 8-char hex code derived from a config_file path, prefixed ff-.
// FNV-1a 32-bit — deterministic, synchronous, no SubtleCrypto needed.
const ffHash = (configFile) => {
    let h = 0x811c9dc5;
    for (let i = 0; i < configFile.length; i++) {
        h ^= configFile.charCodeAt(i);
        h = Math.imul(h, 0x01000193) >>> 0;
    }
    return `ff-${h.toString(16).padStart(8, '0')}`;
};

// 16-char hex fingerprint of a JS object using two FNV-1a passes with different seeds.
// Replaces the previous crypto.subtle SHA-256 approach — synchronous, no async needed.
const fingerprintObject = (obj) => {
    const s = JSON.stringify(obj, Object.keys(obj).sort());
    let h1 = 0x811c9dc5;
    let h2 = 0x04c11db7;
    for (let i = 0; i < s.length; i++) {
        const c = s.charCodeAt(i);
        h1 ^= c;
        h1 = (h1 * 0x01000193) >>> 0;
        h2 ^= c;
        h2 = (h2 * 0x01000193) >>> 0;
    }
    return h1.toString(16).padStart(8, '0') + h2.toString(16).padStart(8, '0');
};

// Stamp a metadata_fingerprint onto config.metadata in-place, then return the config.
const stampMetadataFingerprint = (config) => {
    if (!config?.metadata) return config;
    const meta = { ...config.metadata };
    delete meta.metadata_fingerprint;
    config.metadata.metadata_fingerprint = fingerprintObject(meta);
    return config;
};

const isEnhancedConfig = (inputJson) => {
    if (inputJson?.game_sets && inputJson?.metadata) {
        return true;
    }
    return false;
};
const enhancedConfig = () => {
    if (window.localStorage.getItem('DEFAULT_GAMES')) {
        const games = JSON.parse(window.localStorage.getItem('DEFAULT_GAMES'));
        if (games?.metadata) {
            return games;
        }
    }
    return null;
};

const findMatchingSetIndex = (searchSet, targetArray) => {
    // Helper function to compare two arrays of words
    const compareWords = (arr1, arr2) => {
        if (arr1.length !== arr2.length) return false;
        return arr1.every((word, index) => word === arr2[index]);
    };

    // Helper function to compare two group objects
    const compareGroups = (group1, group2) => {
        return (
            group1.category === group2.category &&
            group1.color === group2.color &&
            compareWords(group1.words, group2.words)
        );
    };

    // Helper function to compare entire sets
    const compareSets = (set1, set2) => {
        if (!(set1.groups.length >= set2.groups.length)) return false;
        return set1.groups.every((group, index) => compareGroups(group, set2.groups[index]));
    };

    // Find the matching index in the target array
    return targetArray.findIndex((set) => compareSets(searchSet, set));
};

// we need a way to distinguish certain click events
const makeCustomClick = (element, category = null, timeout = 0, options = null) => {
    let customEvent = new PointerEvent('click', options);
    customEvent.__defineGetter__('srcElement', () => {
        return category;
    });
    customEvent.__defineGetter__('customEvent', () => {
        return true;
    });
    setTimeout(() => element?.dispatchEvent(customEvent), timeout);
};

const DaveEvent = (detail = {}) => {
    return new CustomEvent('DaveEvent', {
        bubbles: true, // Event bubbles up through the DOM
        cancelable: true, // Event can be canceled
        detail: detail, // Custom data passed with the event
    });
};

const makeCustomDaveClick = (element, category = null, timeout = 0, options = null) => {
    let daveEvent = DaveEvent({
        category: category,
        isCustom: true,
        timestamp: Date.now(),
        ...options,
    });

    // Add custom getters if needed
    daveEvent.__defineGetter__('srcElement', () => {
        return category;
    });

    setTimeout(() => element?.dispatchEvent(daveEvent), timeout);
};

const clickRetry = () => {
    let customEvent = new PointerEvent('click', { shiftKey: false });
    customEvent.__defineGetter__('srcElement', () => {
        return category;
    });
    customEvent.__defineGetter__('customEvent', () => {
        return true;
    });
    const resetBtn = document.getElementById('reset');
    setTimeout(() => resetBtn?.dispatchEvent(customEvent), 200);
};

const linkOutSVG = () => {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
    <path
        fill-rule="evenodd"
        d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 0-1z"
    />
    <path
        fill-rule="evenodd"
        d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"
    />
</svg>`;
};

// enable the user to use keyboard short cuts - see the Help for what...
class KeyComboHandler {
    static MODIFIERS = {
        SHIFT: 'shift',
        ALT: 'alt',
        CTRL: 'ctrl',
        META: 'meta',
    };

    static onKeyCombo =
        (...combinations) =>
        (callback) =>
        (event) => {
            // Allow the combinations array to handle strings or arrays
            const normalizedCombos = combinations.map((combo) =>
                Array.isArray(combo) ? combo : combo.toLowerCase().split('+'),
            );

            // Check any combination matches
            const isMatch = normalizedCombos.some((combo) => {
                const requiredModifiers = {
                    shift: combo.includes(KeyComboHandler.MODIFIERS.SHIFT),
                    alt: combo.includes(KeyComboHandler.MODIFIERS.ALT),
                    ctrl: combo.includes(KeyComboHandler.MODIFIERS.CTRL),
                    meta: combo.includes(KeyComboHandler.MODIFIERS.META),
                };

                // Get non-modifier keys from combo
                const requiredKeys = combo.filter((key) => !Object.values(KeyComboHandler.MODIFIERS).includes(key));

                // Check modifiers match exactly
                const modifiersMatch =
                    event.shiftKey === requiredModifiers.shift &&
                    event.altKey === requiredModifiers.alt &&
                    event.ctrlKey === requiredModifiers.ctrl &&
                    event.metaKey === requiredModifiers.meta;

                // Check if all required keys are pressed
                const keysMatch =
                    requiredKeys.length === 0 || (event.key && requiredKeys.includes(event.key.toLowerCase()));

                return modifiersMatch && keysMatch;
            });

            // it's a match, do something
            if (isMatch) {
                callback(event);
            }
        };

    // Helper method for creating key combo strings
    static createCombo(...keys) {
        return keys.join('+').toLowerCase();
    }
}

// noopener prevents the opened page accessing window.opener (XSS vector);
// noreferrer suppresses the Referer header and implies noopener in modern browsers
const WINDOW_FEATURES = 'noopener,noreferrer';

// windowName controls reuse: '_blank' always opens fresh; a stable name reuses the same tab/window
const openNewLocation = (url, windowName = '_blank', features = WINDOW_FEATURES) => {
    if (url === undefined) return;
    window.open(url, windowName, features);
};

// Opens themes.html in a dedicated named window so repeated clicks reuse it rather than stacking tabs
const openLibrary = (baseUrl) => openNewLocation(baseUrl, 'themes');
const openThemes = openLibrary;

const onMobile = (game) => {
    console.log(`onMobile ${game?.detector.isMobile()}`);
    return game?.detector.isMobile() || false;
};

// we are not responsive so need a way to discover device type to alert the user
class MobileDetector {
    constructor() {
        this._isMobileCache = null;
        this._deviceTypeCache = null;

        this.isMobile = this.isMobile.bind(this);
        this.getDeviceType = this.getDeviceType.bind(this);

        // Initialize media query matcher
        this.mobileQuery = window.matchMedia('(max-width: 767px), (hover: none)');

        // Reset cache when orientation changes or window resizes
        window.addEventListener('resize', () => this._resetCache());
        window.addEventListener('orientationchange', () => this._resetCache());
    }

    _resetCache() {
        this._isMobileCache = null;
        this._deviceTypeCache = null;
    }

    _hasTouch() {
        return (
            'ontouchstart' in window ||
            navigator.maxTouchPoints > 0 ||
            // @ts-ignore
            navigator.msMaxTouchPoints > 0
        );
    }

    _checkUserAgent() {
        const ua = navigator.userAgent.toLowerCase();
        const mobileKeywords = [
            'mobile',
            'android',
            'iphone',
            'ipad',
            'ipod',
            'blackberry',
            'windows phone',
            'webos',
            'opera mini',
            'opera mobi',
            'samsung',
        ];

        return mobileKeywords.some((keyword) => ua.includes(keyword));
    }

    _checkScreenCharacteristics() {
        const { width, height } = window.screen;
        const smallerDimension = Math.min(width, height);
        const largerDimension = Math.max(width, height);

        // Most mobile devices have one dimension under 1024px
        const isTypicalMobileSize = smallerDimension <= 1024;

        // Check for typical mobile aspect ratios
        const aspectRatio = largerDimension / smallerDimension;
        const isTypicalMobileRatio = aspectRatio >= 1.6 && aspectRatio <= 2.1;

        return isTypicalMobileSize || isTypicalMobileRatio;
    }

    _checkPlatform() {
        const platform = navigator?.platform?.toLowerCase();
        const mobilePlatforms = ['iphone', 'ipod', 'ipad', 'android', 'blackberry', 'webos', 'linux armv'];

        return mobilePlatforms.some((p) => platform.includes(p));
    }

    _checkHoverCapability() {
        // Check if the device supports hover using media query
        const hasHover = window.matchMedia('(hover: hover)').matches;
        const noHover = window.matchMedia('(hover: none)').matches;

        return noHover || !hasHover;
    }

    initialised() {
        return typeof (this._deviceTypeCache !== 'undefined') && this._deviceTypeCache !== null;
    }

    // main API
    isMobile() {
        // Return cached result first if available
        if (this._isMobileCache !== null) {
            return this._isMobileCache;
        }

        // Combine multiple detection methods
        const checks = [
            this._checkUserAgent(),
            this._hasTouch(),
            this._checkScreenCharacteristics(),
            this._checkPlatform(),
            this._checkHoverCapability(),
            this.mobileQuery.matches,
        ];

        // This users device is considered mobile if majority of these checks pass
        const mobileChecksPassed = checks.filter(Boolean).length;
        this._isMobileCache = mobileChecksPassed >= 3;

        return this._isMobileCache;
    }

    /**
     * Get more specific device type info
     * @returns {'mobile'|'tablet'|'desktop'}
     */
    getDeviceType() {
        if (this._deviceTypeCache !== null) {
            return this._deviceTypeCache;
        }

        const ua = navigator.userAgent.toLowerCase();
        const width = window.screen.width;
        const height = window.screen.height;
        const smallerDimension = Math.min(width, height);

        // Tablets
        const isTablet =
            (this._hasTouch() && smallerDimension > 640) ||
            ua.includes('ipad') ||
            (ua.includes('android') && !ua.includes('mobile')) ||
            ua.includes('tablet');

        // Cache and return result
        this._deviceTypeCache = isTablet ? 'tablet' : this.isMobile() ? 'mobile' : 'desktop';
        return this._deviceTypeCache;
    }

    /**
     * Add a listener for device type changes
     * Useful for responsive behavior
     */
    onDeviceTypeChange(callback) {
        const handleChange = () => {
            this._resetCache();
            callback(this.getDeviceType());
        };

        window.addEventListener('resize', handleChange);
        window.addEventListener('orientationchange', handleChange);

        // Return cleanup function
        return () => {
            window.removeEventListener('resize', handleChange);
            window.removeEventListener('orientationchange', handleChange);
        };
    }
}

const createGameDataTable = (gameData) => {
    const addStyles = () => {
        const style = document.createElement('style');
        style.textContent = `
            .resource-table-container {
                width: 100%;
                overflow-x: auto;
                margin: 20px 0;
            }

            .mdl-data-table {
                min-width: 800px;
                width: 100%;
                table-layout: fixed;
            }

            .resource-cell-theme {
                width: 15%;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .resource-cell-category {
                width: 20%;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .resource-cell-category-link {
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .resource-cell-word {
                width: 20%;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .resource-cell-urls {
                width: 45%;
                overflow: hidden;
            }

            .resource-cell-url-link {
                display: inline-block;
                max-width: 280px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                vertical-align: middle;
                margin: 2px 4px;
                text-decoration: none;
                color: rgb(63, 81, 181);
            }

            .resource-cell-url-link:hover {
                text-decoration: none;
            }

            .color-row {
                transition: opacity 0.2s ease-in-out;
            }

            .color-row:hover {
                opacity: 0.9;
            }

            .color-row td {
                color: #000000;
                border-top: 1px solid rgba(0, 0, 0, 0.12);
                border-bottom: 1px solid rgba(0, 0, 0, 0.12);
            }

            .color-row.dark-bg td {
                color: #ffffff;
            }

            .color-row.dark-bg .resource-cell-url-link {
                color: #ffffff;
            }

            .hidden-row {
                display: none;
            }

            .search-container {
                flex: 1;
                margin-left: 20px;
                right: 0;
                position: absolute;
                top: 0.1em;
                width: 40%;
            }

            .search-input {
                width: 100%;
                max-width: 500px;
                padding: 8px;
                padding-left: 36px;
                border: none;
                border-bottom: 1px solid rgba(0, 0, 0, 0.12);
                background-color: transparent;
                font-size: 16px;
                outline: none;
                transition: border-color 0.2s ease;
            }

            .search-input:focus {
                border-bottom-color: rgb(63, 81, 181);
            }

            .search-icon {
                position: absolute;
                right: 8px;
                top: 50%;
                transform: translateY(-50%);
                color: rgba(0, 0, 0, 0.54);
            }

            .card-header {
                display: flex;
                align-items: center;
                padding: 16px;
            }

            .title-container {
                padding: 0;
                padding-right: 16px;
                position: relative;
                top: 0.4em;
            }

            .resources-search {
                padding: 0;
                padding-right: 16px;
                margin-bottom: 1em;
            }

            @media screen and (max-width: 800px) {
                .mdl-card__supporting-text {
                    padding: 8px;
                }
            }

            .modal-header>h2 {
                font-size: 2.5em;
            }

`;
        document.head.appendChild(style);
    };

    // Helper function to determine if background color is dark
    const isColorDark = (color) => {
        return false;
        //console.log(`isColorDark color ${color}`);
        // Convert color names to hex
        const colorMap = {
            red: '#f44336',
            blue: '#2196f3',
            green: '#4caf50',
            yellow: '#ffeb3b',
        };
        const colorMavp = {
            blue: '#0000ff',
            green: '#008000',
            indigo: '#4b0082',
            orange: '#ffa500',
            purple: '#800080',
            red: '#ff0000',
            teal: '#008080',
            yellow: '#ffff00',
        };
        const hex = colorMap[color.toLowerCase()] || color;

        // Convert hex to RGB
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);

        // Calculate relative luminance
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

        return luminance < 0.6;
    };

    // simple search effort
    const filterTable = (searchTerm, rows) => {
        searchTerm = searchTerm.toLowerCase();
        rows.forEach((row) => {
            const text = row.textContent.toLowerCase();
            row.classList.toggle('hidden-row', !text.includes(searchTerm));
        });
    };

    // Helper function to flatten the data structure
    const flattenGameData = (data) => {
        const flattened = [];

        data.game_sets.forEach((gameSet) => {
            gameSet.group_sets.forEach((groupSet) => {
                groupSet.forEach((item) => {
                    item.words.forEach((word) => {
                        flattened.push({
                            theme: gameSet.theme,
                            category: item.category,
                            word: word,
                            color: item.color,
                            url: item.url,
                            url_last: [...item.additional_sources].slice(-1),
                            urls: [...item.additional_sources],
                        });
                    });
                });
            });
        });

        return flattened;
    };

    const createLinkAnchor = (url, text, className, title = null) => {
        const link = document.createElement('a');
        link.href = url;
        link.className = className;
        link.textContent = text;
        link.dataset.tooltip = title || url;
        link.classList.add('tooltip');
        link.target = '_blank';
        return link;
    };

    // Create the table structure
    const createTable = (flatData) => {
        const tableContainer = document.createElement('div');
        tableContainer.className = 'resource-table-container';

        const table = document.createElement('table');
        table.className = 'mdl-data-table mdl-js-data-table mdl-shadow--2dp';

        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        ['Theme', 'Category', 'Word', 'Resources'].forEach((text, index) => {
            const th = document.createElement('th');
            th.className = `mdl-data-table__cell--non-numeric resource-cell=header resource-cell-${
                index === 3 ? 'urls' : index === 0 ? 'theme' : index === 1 ? 'category' : 'word'
            }`;
            th.textContent = text;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create body
        const tbody = document.createElement('tbody');
        flatData.forEach((item) => {
            const row = document.createElement('tr');

            const colorMap = {
                red: '#ffcdd2', // Light Red
                blue: '#bbdefb', // Light Blue
                green: '#c8e6c9', // Light Green
                yellow: '#fff9c4', // Light Yellow
                indigo: '#4b0082',
                orange: '#ffa500',
                purple: '#800080',
                teal: '#008080',
            };
            //console.log(`flatData.each ${item} item.color ${item.color}`);
            const bgColor = colorMap[item.color.toLowerCase()];
            row.className = `color-row ${isColorDark(bgColor) ? 'dark-bg' : ''}`;
            row.style.backgroundColor = getRGBA(item.color.toLowerCase(), 0.1);

            // Theme cell
            const themeCell = document.createElement('td');
            themeCell.className = 'mdl-data-table__cell--non-numeric resource-cell-theme';
            themeCell.title = item.theme; // Add tooltip for full text
            themeCell.textContent = item.theme;
            row.appendChild(themeCell);

            // Category cell
            const categoryCell = document.createElement('td');
            categoryCell.className =
                'mdl-data-table__cell--non-numeric resource-cell-category resource-cell-category-link';

            const link = createLinkAnchor(
                item.url_last,
                item.category,
                categoryCell.className,
                `${item.category} - ${item.url_last}`,
            );

            categoryCell.title = item.category;
            //categoryCell.textContent = item.category;
            categoryCell.appendChild(link);
            row.appendChild(categoryCell);

            // Word cell
            const wordCell = document.createElement('td');
            wordCell.className = 'mdl-data-table__cell--non-numeric resource-cell-word';
            wordCell.title = item.word;
            wordCell.textContent = item.word;
            row.appendChild(wordCell);

            // URLs cell
            const urlsCell = document.createElement('td');
            urlsCell.className = 'mdl-data-table__cell--non-numeric resource-cell-urls';

            // Create links for each URL
            item.urls.forEach((url, index) => {
                const className = `resource-cell-url-link resource-cell-url-link-${index}`;
                const link = createLinkAnchor(url, url, className);
                urlsCell.appendChild(link);

                // Add spacing between links
                if (index < item.urls.length - 1) {
                    urlsCell.appendChild(document.createElement('br'));
                }
            });

            row.appendChild(urlsCell);
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        tableContainer.appendChild(table);

        return { tableContainer, tbody };
    };

    // Re-run on every game data change so the resources table stays in sync
    addStyles();

    const flattenedData = flattenGameData(gameData);
    const { tableContainer, tbody } = createTable(flattenedData);

    document.querySelector('.resources-modal h2').className = 'mdl-card__title-text';
    document.querySelector('.resources-modal h2').textContent = 'Sources & Links';

    // Create a container with header
    const container = document.createElement('div');
    container.className = 'resources-table-container mdl-card';
    container.style.width = '100%';

    // Create header div with a search capability
    const header = document.createElement('div');
    header.className = 'card-header resources-search';

    // Header main
    const titleContainer = document.createElement('div');
    titleContainer.className = 'mdl-card__title-text title-container';
    titleContainer.textContent = 'Info sources';

    // Search container
    const searchContainer = document.createElement('div');
    searchContainer.className = 'search-container';

    // Search icon - md
    const searchIcon = document.createElement('span');
    searchIcon.className = 'material-icons search-icon';
    searchIcon.textContent = 'search';

    // Search input - on keypress run the filter
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'search-input';
    searchInput.placeholder = 'Search...';
    searchInput.addEventListener('input', (e) => {
        filterTable(e.target.value, Array.from(tbody.getElementsByTagName('tr')));
    });

    searchContainer.appendChild(searchInput);
    searchContainer.appendChild(searchIcon);

    header.appendChild(titleContainer);
    header.appendChild(searchContainer);
    container.appendChild(header);

    // Add the info table into a scrollable container
    const tableContainer2 = document.createElement('div');
    tableContainer2.className = 'mdl-card__supporting-text';
    tableContainer2.style.width = '100%';
    tableContainer2.style.padding = '0';
    tableContainer2.appendChild(tableContainer);
    container.appendChild(tableContainer2);
    // Doneski
    return container;
};

// Game Manager Class for handling game editing and validation
class GameManager {
    constructor(game) {
        this.game = game;
        this.editingIndex = null;
    }

    themeElement = `<div class="group-theme-editor">
    <div class="editor-group-theme-header">
        <div class="group-theme">
            <label>Theme</label>
            <input type="text" class="group-theme-input" placeholder="Group theme">
        </div>    </div>
    </div>`;
    createEditorHTML() {
        const defaultColors = ['red', 'yellow', 'green', 'blue'];
        const allColors = ['red', 'yellow', 'green', 'blue', 'purple', 'teal', 'orange', 'indigo'];
        return `${this.themeElement}
            ${[0, 1, 2, 3]
                .map(
                    (i) => `
                <div class="group-editor" data-group="${i}">
                    <div class="editor-header">
                        <div class="input-group">
                            <label>Category ${i + 1}</label>
                            <input type="text" class="category-input" placeholder="Category name">
                        </div>
                        <select class="color-select">
                            ${allColors.map((c) => `<option${c === defaultColors[i] ? ' selected' : ''} value="${c}">${c.charAt(0).toUpperCase() + c.slice(1)}</option>`).join('\n                            ')}
                        </select>
                    </div>
                    <div class="word-input-group">
                        ${[0, 1, 2, 3]
                            .map(
                                (j) => `
                            <div class="input-group">
                                <input type="text" class="word-input"
                                       placeholder="Word ${j + 1}"
                                       data-group="${i}"
                                       data-word="${j}">
                            </div>
                        `,
                            )
                            .join('')}
                    </div>
                    <div class="group-meta-editor">
                        <div class="input-group">
                            <label>Description</label>
                            <input type="text" class="description-input" placeholder="Short description of this group">
                        </div>
                        <div class="input-group">
                            <label>Primary URL</label>
                            <input type="text" class="url-input" placeholder="https://...">
                        </div>
                        <div class="input-group">
                            <label>Skill Level</label>
                            <select class="skill-level-select">
                                <option value="Beginner">Beginner</option>
                                <option value="Intermediate" selected>Intermediate</option>
                                <option value="Advanced">Advanced</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Additional Sources (one URL per line)</label>
                            <textarea class="additional-sources-input" rows="3" placeholder="https://..."></textarea>
                        </div>
                    </div>
                </div>
            `,
                )
                .join('')}
        `;
    }

    getEditorData() {
        const groups = [];
        const groupElements = document.querySelectorAll('.group-editor');
        const groupThemeEl = document.querySelector('.group-theme-editor');
        const groupThemeInput = groupThemeEl.querySelector('.group-theme-input');
        const groupThemeName = groupThemeInput.value;
        const game_set_id = groupThemeEl.getAttribute('game-set-id');
        groupElements.forEach((groupEl) => {
            const group_set_id = groupEl.getAttribute('group-set-id');
            const group_item_id = groupEl.getAttribute('group-item-id');
            const category = groupEl.querySelector('.category-input').value;
            const color = groupEl.querySelector('.color-select').value.toLowerCase();
            const words = Array.from(groupEl.querySelectorAll('.word-input')).map((input) =>
                input.value.trim().toUpperCase(),
            );
            const description = groupEl.querySelector('.description-input').value.trim();
            const url = groupEl.querySelector('.url-input').value.trim();
            const skill_level = groupEl.querySelector('.skill-level-select').value;
            const additional_sources = groupEl
                .querySelector('.additional-sources-input')
                .value.split('\n')
                .map((s) => s.trim())
                .filter(Boolean);
            groups.push({
                category,
                color,
                words,
                groupThemeName,
                game_set_id,
                group_set_id,
                group_item_id,
                description,
                url,
                skill_level,
                additional_sources,
            });
        });

        return { game_set_id, groups, groupThemeName };
    }

    setEditorData(gameSets, index = null) {
        const game = gameSets[index];
        const groupThemeEl = document.querySelector('.group-theme-editor');
        const groupThemeInput = groupThemeEl.querySelector('.group-theme-input');

        const group_set_index = 0;
        groupThemeInput.value = game.theme;
        groupThemeEl.setAttribute('game-set-id', game.game_set_id);
        game.group_sets[group_set_index].forEach((group, i) => {
            const groupEl = document.querySelector(`[data-group="${i}"]`);
            groupEl.setAttribute('game-set-id', game.game_set_id);
            groupEl.setAttribute('group-set-id', group.group_set_id);
            groupEl.setAttribute('group-item-id', group.group_item_id);
            groupEl.querySelector('.category-input').value = group.category;
            groupEl.querySelector('.color-select').value = group.color.toLowerCase();
            groupEl.style.backgroundColor = getRGBA(group.color.toLowerCase(), 0.1);
            groupEl.querySelector('.description-input').value = group.description || '';
            groupEl.querySelector('.url-input').value = group.url || '';
            groupEl.querySelector('.skill-level-select').value = group.skill_level || 'Intermediate';
            groupEl.querySelector('.additional-sources-input').value = (group.additional_sources || []).join('\n');
            const wordInputs = groupEl.querySelectorAll('.word-input');
            const wordsLimited = limitList(group.words, wordInputs.length);

            wordsLimited.forEach((word, j) => {
                wordInputs[j].value = word;
            });
        });
    }
}

// The model dialog used for Help, Editing etc
class ModalManager {
    constructor() {
        this.activeModals = new Set();
        this.setupKeyboardListener();
        this.setupClickOutListener();
    }

    setupKeyboardListener() {
        document.addEventListener(
            'keydown',
            (e) => {
                if (e.key === 'Escape') {
                    this.closeTopModal();
                }
            },
            false,
        );
    }

    setupClickOutListener() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeTopModal();
            }
        });
    }

    closeTopModal() {
        if (this.activeModals.size > 0) {
            const topModal = Array.from(this.activeModals).pop();
            this.hideModal(topModal);
        }
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        const modalContent = modal.querySelector(`.${modalId}`);
        if (!modal) return;

        // Add close button if it doesn't exist already
        if (!modal.querySelector('.modal-close')) {
            const header = modalContent.querySelector('h2');
            const closeBtn = document.createElement('button');
            closeBtn.className = 'modal-close';
            closeBtn.innerHTML = '×';
            closeBtn.onclick = () => this.hideModal(modalId);
            const headerDiv = document.createElement('div');
            headerDiv.className = 'modal-header dynamic-add';

            // Move the existing h2 into the header div
            if (header) {
                header.parentNode.removeChild(header);
                headerDiv.appendChild(header);
            }
            headerDiv.appendChild(closeBtn);

            modalContent.insertBefore(headerDiv, modalContent.firstChild);
        }

        modal.classList.add('visible');
        modalContent.classList.add('visible');
        document.body.style.overflow = 'hidden';
        this.activeModals.add(modalId);
    }

    isModalVisible(modalId) {
        const modal = document.getElementById(modalId);
        return modal && modal.classList.contains('visible');
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        const modalContent = modal.querySelector(`.${modalId}`);
        if (!modal) return;

        modal.classList.remove('visible');
        modalContent.classList.remove('visible');
        this.activeModals.delete(modalId);

        if (this.activeModals.size === 0) {
            document.body.style.overflow = '';
        }
    }

    toggleModal(modalId) {
        if (this.isModalVisible(modalId)) {
            this.hideModal(modalId);
        } else {
            this.showModal(modalId);
        }
    }
}

// Main Game Class
class ConnectionsGame {
    constructor(config = DEFAULT_GAMES) {
        this.linkOutSVG = linkOutSVG;
        this.config = config;
        this.gameSets = this.config?.game_sets || [];
        this.gameMetadata = this.config?.metadata;
        this.detector = new MobileDetector();
        this.gameManager = new GameManager(this);
        this.selectedWords = new Set();
        this.solvedGroups = new Set();
        this.lives = parseInt(window.urlParams.get('lives')) || DEFAULT_LIVES;

        this.hintsLeft = parseInt(window.urlParams.get('hints')) || DEFAULT_HINTS;
        this.gameActive = true;
        this.highScores = JSON.parse(localStorage.getItem('connectionHighScores') || '{}');

        this.currentRoundIndex = 0;
        this.setupEventListeners();
        this.setupMobileEventListeners();
        this.setupGameManagement();
        this.startNewGame(0);
        this.setupLevelSelect();
        this.addSolveHandler();
        this.modalManager = new ModalManager();
        window.find4 = this;
    }

    _dzReasons = new Set();

    setDropZoneVisible(reason, visible) {
        const el = document.querySelector('.drop-zone');
        if (!el) return;
        if (visible) this._dzReasons.add(reason);
        else this._dzReasons.delete(reason);
        el.classList.toggle('dz-visible', this._dzReasons.size > 0);
    }

    toggleToolbar = () => {
        const section = document.getElementById('toolbar-section');
        const toggle = document.getElementById('toolbar-toggle');
        section.classList.toggle('section-collapsed');
        const isActive = !section.classList.contains('section-collapsed');
        toggle.classList.toggle('active', isActive);
        this.setDropZoneVisible('toolbar', isActive);
    };

    optionsCombo = KeyComboHandler.onKeyCombo(...[KeyComboHandler.createCombo('ctrl', 'shift', 'o')])((event) => {
        this.toggleToolbar();
        window.find4.showMessage('Toggling toolbar', 'success');
        console.log(event);
    });

    optionsComboSolve = KeyComboHandler.onKeyCombo(...[KeyComboHandler.createCombo('ctrl', 'shift', 's')])((event) => {
        makeCustomClick(document.getElementById('solve'));
        window.find4.showMessage('Auto solving the full game', 'success');
        console.log(event);
    });

    optionsComboExport = KeyComboHandler.onKeyCombo(...[KeyComboHandler.createCombo('ctrl', 'shift', 'e')])((event) => {
        document.querySelector('.export-btn').dispatchEvent(new Event('click'));
        window.find4.showMessage('Exporting puzzles as json to Downloads', 'success');
        console.log(event);
    });

    optionsComboHelp = KeyComboHandler.onKeyCombo(...[KeyComboHandler.createCombo('ctrl', 'shift', 'h')])((event) => {
        this.modalManager.toggleModal('tutorial-modal');
        window.find4.showMessage('Toggling the help page', 'success');
        console.log(event);
    });

    optionsComboResources = KeyComboHandler.onKeyCombo(...[KeyComboHandler.createCombo('ctrl', 'shift', 'd')])(
        (event) => {
            this.modalManager.toggleModal('resources-modal');
            window.find4.showMessage('Toggling Sources & Resources for the Theme', 'success');
            console.log(event);
        },
    );

    optionsComboLibrary = KeyComboHandler.onKeyCombo(...[KeyComboHandler.createCombo('ctrl', 'shift', 'l')])(
        (event) => {
            //document.querySelector('.library-btn').dispatchEvent(new Event('click'));
            makeCustomDaveClick(document.getElementById('library'));
            //            window.find4.openResourceTable();
            window.find4.showMessage('Showing Available themes', 'success');
            console.log(event);
        },
    );

    optionsComboNew = KeyComboHandler.onKeyCombo(...[KeyComboHandler.createCombo('ctrl', 'shift', 'n')])((event) => {
        this.modalManager.toggleModal('editor-modal');
        window.find4.showMessage('Toggling game editor', 'success');
        console.log(event);
    });

    toggleGameSource = async () => {
        const current = localStorage.getItem('GAME_SOURCE') || 'default';
        const next = current === 'default' ? 'library' : 'default';
        const url = next === 'library' ? '/library/library.json' : '/config/default.json';
        localStorage.setItem('GAME_SOURCE', next);

        window.find4.showMessage(`Switching to ${next} game source...`, 'success', 4000);
        console.log(`GAME_SOURCE toggle: ${current} -> ${next}`);

        const result = await loadConfig({ url });
        if (!result.success) {
            window.find4.showMessage(`Failed to load ${url} (${result.status || 'network error'})`, 'error', 5000);
            return;
        }

        const gamesTransformed = transformJson(result.config);
        const potentialGames = JSON.parse(JSON.stringify(gamesTransformed));
        const validationResult = validateGame(potentialGames);
        if (validationResult !== true) {
            window.find4.showMessage(`${next} config failed validation: ${validationResult}`, 'error', 5000);
            return;
        }

        const stampedGames = stampMetadataFingerprint(potentialGames);
        localStorage.setItem('GAME_SOURCE', next);
        localStorage.setItem('DEFAULT_GAMES', JSON.stringify(stampedGames));
        DEFAULT_GAMES = stampedGames;
        this.config = potentialGames;
        this.gameSets = potentialGames.game_sets || [];
        this.updateGameSets();
        this.startNewGame(0);
        window.find4.showMessage(`Loaded ${this.gameSets.length} game(s) from ${next} source`, 'success', 4000);
        const sourceBtn = document.getElementById('mobile-game-source-btn');
        if (sourceBtn) {
            const afterNext = next === 'library' ? 'Default' : 'Library';
            sourceBtn.querySelector('span').textContent = `Switch to ${afterNext}`;
        }
    };

    optionsComboGameSource = KeyComboHandler.onKeyCombo(...[KeyComboHandler.createCombo('ctrl', 'shift', 'g')])(
        async (event) => {
            await this.toggleGameSource();
        },
    );

    deleteStorageComboNew = KeyComboHandler.onKeyCombo(...[KeyComboHandler.createCombo('ctrl', 'shift', 'x')])(
        (event) => {
            if (confirm('Delete ALL saved games from localStorage? This cannot be undone.')) {
                localStorage.clear();
                document.querySelectorAll('.game-set').forEach((el) => el.remove());
                this.gameSets = [];
                this.startNewGame(0);
                window.find4.showMessage('All saved games deleted from localStorage', 'error');
            }
        },
    );

    optionsComboShift = KeyComboHandler.onKeyCombo(...[KeyComboHandler.createCombo('shift')])((event) => {
        window.find4.showMessage('Click or Tap any word to solve that grouping', 'success');
        console.log(event);
    });

    goHome = () => {
        const baseUrl = `${window.location.origin}`;
        const newUrl = `${baseUrl}/index.html`;
        openNewLocation(newUrl);
    };

    findCategoryForWord = (word) => {
        let category = null;
        // Loop through each category/group in currentGame
        this.currentGame.forEach((group) => {
            // Check if word exists in this group's words
            if (group.words.includes(word) && category === null) {
                category = group.category;
            }
        });
        // Return null if word not found in any category
        return category;
    };

    asConfig = () => {
        const games = JSON.parse(window.localStorage.getItem('DEFAULT_GAMES'));
        if (games?.metadata && games?.game_sets && games?.id_registry) {
            return {
                metadata: games?.metadata,
                game_sets: games.game_sets,
                id_registry: games.id_registry,
            };
        }
        throw new Error('config is missing from localStorage');
    };

    enhancedConfig = () => {
        if (localStorage.getItem('DEFAULT_GAMES')) {
            const games = JSON.parse(localStorage.getItem('DEFAULT_GAMES'));
            if (games?.metadata) {
                return games;
            }
        }
        return null;
    };

    openGameEditor(index = null) {
        this.gameManager.editingIndex = index;
        const editor = document.getElementById('game-editor');
        editor.innerHTML = this.gameManager.createEditorHTML();

        if (index !== null) {
            this.gameManager.setEditorData(this.gameSets, index);
        } else {
            const defaultColors = ['red', 'yellow', 'green', 'blue'];
            document.querySelectorAll('.group-editor').forEach((groupEl, i) => {
                groupEl.style.backgroundColor = getRGBA(defaultColors[i], 0.1);
            });
        }

        editor.addEventListener('change', (e) => {
            if (e.target.classList.contains('color-select')) {
                e.target.closest('.group-editor').style.backgroundColor = getRGBA(e.target.value, 0.1);
            }
        });

        this.modalManager.showModal('editor-modal');
        document.querySelector('.dynamic-add').prepend(document.querySelector('.editor-button-group'));
    }

    openResourceTable() {
        this.modalManager.showModal('resources-modal');
    }

    closeResourceTable() {
        this.modalManager.hideModal('resources-modal');
    }

    openTutorial() {
        this.modalManager.showModal('tutorial-modal');
    }

    closeTutorial() {
        this.modalManager.hideModal('tutorial-modal');
    }

    // Add method to toggle modal visibility
    toggleModal(modalId) {
        this.modalManager.toggleModal(modalId);
    }

    addSolveHandler = () => {
        document.querySelector('.solve-btn')?.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();

            // shift+click on a word tile dispatches a custom click to the solve btn with
            // srcElement set to the category name — that's how we solve a single group
            const category = e?.shiftKey && e?.srcElement ? e.srcElement : null;
            const solveBtn = document.querySelector('.solve-btn');
            solveBtn.disabled = category ? false : true;

            await this.autoSolver(category);
        });
    };

    autoSolver = async (category = null) => {
        setTimeout(() => {
            const msg = category ? `Auto solving the "${category}" category` : 'Auto solving all game categories';
            this.showMessage(msg, 'success', 4000);
        }, 500);

        const fireClick = (el) => {
            const event = new PointerEvent('click');
            event.__defineGetter__('srcElement', () => null);
            event.__defineGetter__('customEvent', () => true);
            setTimeout(() => el?.dispatchEvent(event), 0);
        };

        for (let group of this.currentGame) {
            if (category && category !== group.category) continue;

            for (let word of group.words) {
                const tile = document.querySelector(`.word-tile[data-word="${word}"]`);
                if (!tile) continue;

                const shouldClick = !category || tile.getAttribute('data-category') === category;
                if (shouldClick) {
                    setTimeout(() => fireClick(tile), 300);
                    await new Promise((resolve) => setTimeout(resolve, AUTO_SOLVE_WORD_DELAY));
                }
            }

            const submitBtn = document.querySelector('.submit-btn');
            if (submitBtn) {
                submitBtn.click();
                await new Promise((resolve) => setTimeout(resolve, AUTO_SOLVE_SUBMIT_DELAY));
            }
        }

        if (!category) {
            document.querySelector('.solve-btn').disabled = true;
        }
    };
    handleStringItem = async (item) =>
        new Promise((resolve) => {
            item.getAsString(async (text) => {
                await this.handlePlainText(text);
                resolve();
            });
        });

    handleFileItem = async (item) => {
        const file = item.getAsFile();
        if (file.type === 'application/zip' || file.name?.endsWith('.zip')) {
            await this.handleZipFile(file);
            return;
        }
        const reader = new FileReader();
        return new Promise((resolve, reject) => {
            reader.onload = async (e) => {
                try {
                    await this.handlePlainText(e.target.result);
                    resolve();
                } catch (err) {
                    reject(err);
                }
            };
            reader.onerror = reject;
            reader.readAsText(file);
        });
    };

    handlePlainText = async (e) => {
        if (!e) {
            console.error('No plainText found');
            return;
        }
        try {
            console.log('handlePlainText e:', e);
            const gamesTransformed = transformJson(hydratePackedGame(JSON.parse(e)));
            const potentialGames = JSON.parse(JSON.stringify(gamesTransformed));
            const validationResult = validateGame(potentialGames);

            if (validationResult === true) {
                this.addGameSet(potentialGames);
                let gameSetsCopy = JSON.parse(JSON.stringify(this.gameSets));
                let games = JSON.parse(window.localStorage.getItem('DEFAULT_GAMES') || 'null');
                if (!games) games = { metadata: this.config?.metadata || {}, game_sets: [] };
                games.game_sets = gameSetsCopy;
                window.localStorage.setItem('DEFAULT_GAMES', JSON.stringify(games));
                this.showMessage('New Game(s) set loaded successfully!', 'success');
                this.startNewGame(0);
            } else {
                console.log(`validation failed ${validationResult}`);
                return;
            }
        } catch (error) {
            console.log('handlePlainText Error parsing file', error);
            this.showMessage(`handlePlainText Error parsing file ${error}`, 'error');
        }
    };
    processItem = async (item) => {
        const { kind, type } = item;
        if (kind === 'string' && type.match('^text/plain')) {
            await this.handleStringItem(item);
        } else if (kind === 'file') {
            await this.handleFileItem(item);
        }
    };

    setupEventListeners() {
        document.getElementById('toolbar-toggle').addEventListener('click', () => this.toggleToolbar());
        document.getElementById('submit').addEventListener('click', () => this.checkSelection());
        document.getElementById('hint').addEventListener('click', () => this.giveHint());
        document.getElementById('shuffle').addEventListener('click', () => this.shuffleGrid());
        document.getElementById('reset').addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();

            this.startNewGame(parseInt(document.getElementById('level-select').value), true);
        });

        // File input handling
        const fileInput = document.getElementById('file-input');
        fileInput.addEventListener('change', (e) => {
            for (const file of e.target.files) this.handleFile(file);
        });

        // Drop zone handling
        const dropZoneTargeted = document.getElementById('drop-zone');
        const dropZone = document.getElementById('body-main');

        if (!onMobile(this)) {
            dropZone.addEventListener('dblclick', (e) => {
                console.log(e);
                fileInput.click();
            });
        }
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
            this.setDropZoneVisible('drag', true);
            this.expandGameSets();
        });
        dropZone.addEventListener('dragleave', (e) => {
            if (dropZone.contains(e.relatedTarget)) return;
            dropZone.classList.remove('drag-over');
            this.setDropZoneVisible('drag', false);
        });
        document.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            this.setDropZoneVisible('drag', false);
            for (const file of e.dataTransfer.files) this.handleFile(file);
        });
        dropZone.addEventListener('paste', (e) => {
            e.preventDefault();
            let l = e.clipboardData || e.originalEvent.clipboardData || window.clipboardData;
            if (!l?.items?.length) {
                console.error('no items found to process');
                return;
            }
            this.setDropZoneVisible('paste', true);
            this.expandGameSets();
            for (let i of l.items) i && this.processItem(i);
            setTimeout(() => this.setDropZoneVisible('paste', false), 2000);
        });

        // Show drop-zone when shift is held for 3+ seconds
        let shiftHoldTimer = null;
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Shift' && !e.repeat && shiftHoldTimer === null) {
                shiftHoldTimer = setTimeout(() => this.setDropZoneVisible('shift', true), 3000);
            }
        });
        document.addEventListener('keyup', (e) => {
            if (e.key === 'Shift') {
                clearTimeout(shiftHoldTimer);
                shiftHoldTimer = null;
                this.setDropZoneVisible('shift', false);
            }
        });

        // Game sets collapse toggle
        document.getElementById('game-sets-header').addEventListener('click', () => {
            this.toggleGameSets();
        });

        // Level select handling
        document.getElementById('level-select').addEventListener('change', (e) => {
            this.startNewGame(parseInt(e.target.value));
        });

        document.addEventListener('keydown', this.optionsCombo, false);
        document.addEventListener('keydown', this.optionsComboSolve, false);
        document.addEventListener('keydown', this.optionsComboExport, false);
        document.addEventListener('keydown', this.optionsComboHelp, false);
        document.addEventListener('keydown', this.optionsComboShift, false);
        document.addEventListener('keydown', this.optionsComboResources, false);
        document.addEventListener('keydown', this.optionsComboLibrary, false);
        document.addEventListener('keydown', this.optionsComboNew, false);
        document.addEventListener('keydown', this.optionsComboGameSource, false);
        document.addEventListener('keydown', this.deleteStorageComboNew, false);

        const libraryEl = document.getElementById('library');

        if (!onMobile(this)) {
            document.querySelector('.toolbar').addEventListener('dblclick', (event) => {
                event.preventDefault();
                event.stopPropagation();
                ['.toolbar-options', '.library-btn'].forEach((selector) => {
                    console.log(document.querySelector(selector).classList);
                    document.querySelector(selector).classList.toggle('hidden');
                });
            });

            libraryEl.addEventListener('DaveEvent', (e) => {
                //event.preventDefault();
                //event.stopPropagation();
                setTimeout(() => {
                    game?.openThemes('themes.html');
                }, 0);
                console.log('DaveEvent', e);
            });
        }

        // document.querySelector('.toolbar').addEventListener('dblclick', (event) => {
        //     event.preventDefault();
        //     event.stopPropagation();
        //     document.querySelector('.toolbar-options').classList.toggle('hidden');
        //     document.querySelector('.resources-btn').classList.toggle('hidden');
        //     document.querySelector('.library-btn').classList.toggle('hidden');
        // });

        document.querySelector('.shift-btn').addEventListener('touchend', (event) => {
            event.preventDefault();
            event.stopPropagation();

            if (virtualShiftKeyPressed()) {
                event.target.disabled = false;
            } else {
                window.find4.showMessage('Click or Tap any word to solve that grouping', 'success');
                event.target.disabled = true;
            }
        });

        // document.querySelector('.mobile-sheet-backdrop').addEventListener('click', (event) => {
        //     event.preventDefault();
        //     event.stopPropagation();
        //     console.log(`.mobile-fab' touchend ${event}`);
        //     if (!event.target.querySelector('.game-grid .word-tile')) {
        //         virtualShiftKeyReset();
        //     }
        // });
        // Reset the virtual shift key on any click outside the word grid (desktop only)
        document.addEventListener('click', (event) => {
            if (window.game.detector.isMobile()) return;
            if (!event.target.querySelector('.game-grid .word-tile')) {
                virtualShiftKeyReset();
            }
        });
    }

    setupMobileEventListeners() {
        console.log(`setupMobileEventListeners() onMobile()=${onMobile(this)}`);

        if (!onMobile(this)) {
            console.log('not on mobile - not setting up mobileHandlers');
            return;
        }

        const fab = document.getElementById('mobile-fab');
        const sheet = document.getElementById('mobile-sheet');
        const backdrop = document.getElementById('mobile-sheet-backdrop');

        const openSheet = () => {
            sheet.classList.add('open');
            backdrop.classList.add('visible');
            fab.classList.add('open');
        };

        window.closeMobileSheet = () => {
            sheet.classList.remove('open');
            backdrop.classList.remove('visible');
            fab.classList.remove('open');
        };

        fab.addEventListener('click', () => {
            sheet.classList.contains('open') ? window.closeMobileSheet() : openSheet();
        });

        backdrop.addEventListener('click', window.closeMobileSheet);

        const sourceBtn = document.getElementById('mobile-game-source-btn');
        if (sourceBtn) {
            const current = localStorage.getItem('GAME_SOURCE') || 'default';
            const next = current === 'default' ? 'Library' : 'Default';
            sourceBtn.querySelector('span').textContent = `Switch to ${next}`;
        }

        const dropZone = document.getElementById('body');
        const fileInput = document.getElementById('file-input');
        const libraryEl = document.getElementById('library');
        const toolbarEl = document.querySelector('.toolbar');
        const dropZoneTargeted = document.getElementById('drop-zone');

        createDblClick(
            dropZoneTargeted,
            (e) => {
                console.log('Double clicked/tapped!', e);
                setTimeout(() => {
                    fileInput.click();
                }, 0);
            },
            400,
        );

        libraryEl.addEventListener('DaveEvent', (e) => {
            e.preventDefault();
            e.stopPropagation();
            setTimeout(() => {
                game?.openNewLocation('themes.html');
            }, 0);
            console.log('DaveEvent', e);
        });
    }

    updateDisplay() {
        // Update lives counter
        document.getElementById('lives').textContent = this.lives;

        // Update hints counter
        document.getElementById('hints-left').textContent = this.hintsLeft;
        document.getElementById('hint').disabled = this.hintsLeft <= 0;

        // Update submit button state
        document.getElementById('submit').disabled = this.selectedWords.size !== 4;

        // Update shuffle button state
        document.getElementById('shuffle').disabled = !this.gameActive;

        // Clear solved categories
        document.getElementById('solved-categories').innerHTML = '';

        // Reset timer display
        document.getElementById('timer').textContent = '00:00';

        // Show current level high score if it exists
        const currentLevel = parseInt(document.getElementById('level-select').value);
        const highScore = this.highScores[currentLevel];
        if (highScore) {
            this.showMessage(`Best Time: ${highScore}`, 'success');
        }

        // Update puzzle count
        document.getElementById('puzzle-count').textContent = this.gameSets.length;

        // Enable/disable controls based on game state
        // Note: 'submit' is intentionally excluded — its state is controlled solely by selectedWords.size
        const controls = ['submit', 'hint', 'shuffle', 'reset', 'solve'];
        //        const controls = ['hint', 'shuffle', 'reset', 'solve', 'resources'];
        const retryBtn = document.getElementById('reset');
        if (retryBtn && !retryBtn.classList.contains('hidden')) {
            retryBtn.classList.add('hidden');
        }
        controls.forEach((id) => {
            const element = document.getElementById(id);
            if (element) {
                element.disabled = id != 'submit' ? !this.gameActive : true;
                element.classList.remove('hidden');
            }
        });
    }

    // Mirrors the top-level openNewLocation -- keeping both because game.openNewLocation()
    // is called from inline onclick handlers in updateGameSets HTML
    openNewLocation(url, windowName = '_blank', features = WINDOW_FEATURES) {
        if (url === undefined) return;
        window.open(url, windowName, features);
    }

    // Opens themes.html in a dedicated named window so repeated clicks reuse it
    openLibrary(url) {
        openLibrary(url);
    }
    openThemes(url) {
        openLibrary(url);
    }

    setupGameManagement() {
        this.setupSortableGameSets();
        this.updateGameCount();
        this.updateGameSets();
    }

    startNewGame(levelIndex, reset = false, roundIndex = 0) {
        this.currentGameIndex = levelIndex;
        this.currentRoundIndex = roundIndex;

        if (!this.gameSets || this.gameSets.length === 0) {
            this.currentGame = [];
            this.game_set_id = null;
            this.gameActive = false;
            this.selectedWords.clear();
            this.solvedGroups.clear();
            this.updateDisplay();
            document.getElementById('game-grid').innerHTML = '';
            this.showMessage('No games loaded. Drop a JSON file or use the Library to get started.', 'info', 5000);
            return;
        }

        this.game_set_id = this.gameSets[levelIndex].game_set_id;
        this.currentGame = this.gameSets[levelIndex].group_sets[roundIndex];
        this.selectedWords.clear();
        this.solvedGroups.clear();
        this.lives = DEFAULT_LIVES;
        this.hintsLeft = parseInt(window.urlParams.get('hints')) || DEFAULT_HINTS;
        this.gameActive = true;
        this.startTime = Date.now();

        const selectEl = document.getElementById('level-select');
        if (selectEl) {
            selectEl.value = levelIndex;
            const selectedOption = selectEl.options[selectEl.selectedIndex];
            if (selectedOption && roundIndex > 0) {
                const totalRounds = this.gameSets[levelIndex]?.group_sets?.length || 1;
                const baseText = selectedOption.dataset.baseText || selectedOption.textContent;
                selectedOption.dataset.baseText = baseText.replace(/ \/ Round \d+/, '');
                selectedOption.textContent = `${selectedOption.dataset.baseText} / Round ${roundIndex + 1}`;
            } else if (selectedOption && selectedOption.dataset.baseText) {
                selectedOption.textContent = selectedOption.dataset.baseText;
                delete selectedOption.dataset.baseText;
            }
        }

        this.updateDisplay();
        this.startTimer();
        this.shuffleAndRenderGrid();

        const newTableContainerEl = createGameDataTable({ game_sets: this.gameSets });

        let gameResourcesInfoEl = document.getElementById('resources-modal-container');
        let oldTableContainerEl = gameResourcesInfoEl?.querySelector('.resources-table-container');
        oldTableContainerEl?.remove();
        gameResourcesInfoEl.appendChild(newTableContainerEl);
    }

    shuffleAndRenderGrid() {
        const allWords = this.currentGame.flatMap((group) => shuffleAndTake(group.words));
        this.shuffledWords = this.shuffle([...allWords]);
        this.renderGrid();
    }

    shuffle(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }
    mouseOverHandler = (event) => {
        const solvedColor = event.target.getAttribute('solved-color').toLowerCase();
        const solvedColorClassname = solvedColor;
        const solvedColorClassnameDot = `.${solvedColorClassname}`;
        const notCategoryGroup = this.findUnsolvedElements(
            document.querySelector('.game-grid-solved-categories'),
            solvedColorClassname,
        );
        //        const notCategoryGroup = this.findUnsolvedElements(event.target.parentElement, solvedColorClassname);
        const notCategorySolvedGroup = this.findUnsolvedElements(
            document.querySelector('.solved-categories'),
            solvedColorClassname,
        );
        const categoryGroup = document.querySelectorAll(solvedColorClassnameDot);
        const categorySolvedGroup = document
            .querySelector('.solved-categories')
            .querySelectorAll(solvedColorClassnameDot);
        const allNotGroup = [...notCategoryGroup, ...notCategorySolvedGroup];
        allNotGroup.forEach((item) => {
            item?.classList.add('word-tile-blur');
        });
        const allGroup = [...categoryGroup, ...categorySolvedGroup];
        allGroup.forEach((item) => {
            item?.classList.add('word-tile-solved-focus');
        });
    };

    // Blur/focus behaviour is currently disabled (early return) — keeping the logic
    // for when I decide if I want it on solved tiles too
    mouseOverHandlerBrief = (event) => {
        const solvedColor = event.target.getAttribute('solved-color')?.toLowerCase();
        const solvedColorClassname = solvedColor;
        const solvedColorClassnameDot = `.${solvedColorClassname}`;
        const notCategoryGroup = this.findUnsolvedElements(
            document.querySelector('.game-grid-solved-categories'),
            solvedColorClassname?.toLowerCase(),
        );
        const notCategorySolvedGroup = this.findUnsolvedElements(
            document.querySelector('.solved-categories'),
            solvedColorClassname?.toLowerCase(),
        );
        const categoryGroup = document.querySelectorAll(solvedColorClassnameDot);
        const categorySolvedGroup = document
            .querySelector('.solved-categories')
            .querySelectorAll(solvedColorClassnameDot.toLowerCase());
        const allNotGroup = [...notCategoryGroup, ...notCategorySolvedGroup];
        return;
        allNotGroup.forEach((item) => {
            item?.classList.add('word-tile-blur');
        });
        const allGroup = [...categoryGroup, ...categorySolvedGroup];
        allGroup.forEach((item) => {
            item?.classList.add('word-tile-solved-focus');
        });
    };

    mouseOutHandler = (event) => {
        const solvedColor = event.target.getAttribute('solved-color').toLowerCase();
        const solvedColorClassname = solvedColor;
        const solvedColorClassnameDot = `.${solvedColorClassname}`;
        const categoryGroup = document.querySelectorAll(solvedColorClassnameDot);
        const categorySolvedGroup = document
            .querySelector('.solved-categories')
            .querySelectorAll(solvedColorClassnameDot);
        const notCategoryGroup = this.findUnsolvedElements(
            document.querySelector('.game-grid-solved-categories'),
            solvedColorClassname,
        );
        const notCategorySolvedGroup = this.findUnsolvedElements(
            document.querySelector('.solved-categories'),
            solvedColorClassname,
        );
        const allNotGroup = [...notCategoryGroup, ...notCategorySolvedGroup];
        allNotGroup.forEach((item) => {
            item?.classList.remove('word-tile-blur');
        });
        const allGroup = [...categoryGroup, ...categorySolvedGroup];
        allGroup.forEach((item) => {
            item?.classList.remove('word-tile-solved-focus');
        });
    };
    // Paired with mouseOverHandlerBrief — both disabled for now, same reason
    mouseOutHandlerBrief = (event) => {
        const solvedColor = event.target.getAttribute('solved-color')?.toLowerCase();
        const solvedColorClassname = solvedColor;
        const solvedColorClassnameDot = `.${solvedColorClassname}`;
        const categoryGroup = document.querySelectorAll(solvedColorClassnameDot);
        const categorySolvedGroup = document
            .querySelector('.solved-categories')
            .querySelectorAll(solvedColorClassnameDot);
        const notCategoryGroup = this.findUnsolvedElements(
            document.querySelector('.game-grid-solved-categories'),
            solvedColorClassname?.toLowerCase(),
        );
        const notCategorySolvedGroup = this.findUnsolvedElements(
            document.querySelector('.solved-categories'),
            solvedColorClassname?.toLowerCase(),
        );
        const allNotGroup = [...notCategoryGroup, ...notCategorySolvedGroup];
        return;
        allNotGroup.forEach((item) => {
            item?.classList.remove('word-tile-blur');
        });
        const allGroup = [...categoryGroup, ...categorySolvedGroup];
        allGroup.forEach((item) => {
            item?.classList.remove('word-tile-solved-focus');
        });
    };
    findUnsolvedElements = (parent, selector) =>
        [...parent.querySelectorAll('.dynamic-item')].filter((el) => !el.classList.contains(selector));

    renderGrid() {
        const grid = document.getElementById('game-grid');
        grid.innerHTML = '';

        this.shuffledWords.forEach((word) => {
            const tile = document.createElement('div');
            const category = this.findCategoryForWord(word);
            tile.className = 'word-tile dynamic-item device-card';
            tile.textContent = word;
            tile.setAttribute('data-word', word);
            category && tile.setAttribute('data-category', category);

            const solvedGroup = Array.from(this.solvedGroups).find((group) => group.words.includes(word));

            if (solvedGroup) {
                tile.setAttribute('solved-color', `solved-${solvedGroup.color.toLowerCase()}`);
                tile.setAttribute('data-tooltip', solvedGroup?.description || solvedGroup.category);
                tile.classList.add(
                    ...[
                        'word-tile',
                        'device-card',
                        'clickable',
                        `solved-${solvedGroup.color.toLowerCase()}`,
                        'tooltip',
                        'your-class',
                    ],
                );

                tile.title = `The Category is "${solvedGroup.category}"`;
                // do we have any urls to send the user to for extra info
                if (solvedGroup.url !== undefined && solvedGroup.additional_sources) {
                    tile.classList.add(...['url-icon']);

                    tile.addEventListener('click', (event) => {
                        virtualShiftKeyReset();
                        event.preventDefault();
                        event.stopPropagation();
                        if (!event?.customEvent) {
                            const dstUrl = solvedGroup?.additional_sources[0] || solvedGroup.url;
                            this.openNewLocation(dstUrl);
                        }
                    });
                    tile.addEventListener('mouseover', this.mouseOverHandler);
                    tile.addEventListener('mouseout', this.mouseOutHandler);
                }
            } else {
                tile.addEventListener('click', (event) => {
                    event.preventDefault();
                    event.stopPropagation();

                    if (event.shiftKey === true || virtualShiftKeyPressed()) {
                        const category = tile.getAttribute('data-category');
                        console.log(`word: ${word} shift: ${event.shiftKey}`, category);

                        makeCustomClick(document.getElementById('solve'), category, 1000, { shiftKey: true });

                        // let customEvent = new PointerEvent('click', { shiftKey: true });
                        // customEvent.__defineGetter__('srcElement', () => {
                        //     return category;
                        // });
                        // customEvent.__defineGetter__('customEvent', () => {
                        //     return true;
                        // });
                        //setTimeout(() => document.getElementById('solve').dispatchEvent(customEvent), 1000);
                    } else {
                        this.toggleWord(word, tile);

                        if (this.selectedWords.has(word)) {
                            tile.classList.add('selected');
                        }
                    }
                    virtualShiftKeyReset();
                });
                tile.addEventListener('mousedown', function (e) {
                    if (e.shiftKey) {
                        e.preventDefault();
                        return false;
                    }
                });
                tile.addEventListener('mouseover', this.mouseOverHandlerBrief);
                tile.addEventListener('mouseout', this.mouseOutHandlerBrief);
            }

            grid.appendChild(tile);
        });
    }

    toggleWord(word, tile) {
        if (!this.gameActive) return;

        if (this.selectedWords.has(word)) {
            this.selectedWords.delete(word);
            tile.classList.remove('selected');
        } else if (this.selectedWords.size < 4) {
            this.selectedWords.add(word);
            tile.classList.add('selected');
        }

        document.getElementById('submit').disabled = this.selectedWords.size !== 4;
    }

    checkSelection() {
        if (!this.gameActive || this.selectedWords.size !== 4) return;

        const selectedWordsArray = Array.from(this.selectedWords);
        const matchingGroup = this.currentGame.find(
            (group) =>
                selectedWordsArray.every((word) => group.words.includes(word)) &&
                !Array.from(this.solvedGroups).some((solved) => solved.words.join(',') === group.words.join(',')),
        );

        if (matchingGroup) {
            this.solveGroup(matchingGroup);
        } else {
            this.handleIncorrectGuess();
        }
    }

    solveGroup(group) {
        this.solvedGroups.add(group);
        this.showMessage('Correct group found!', 'success');

        setTimeout(() => this.showMessage(`Connection is: ${group.category}`, 'success'), 3000);

        if (this.solvedGroups.size === 4) {
            this.endGame(true);
        }

        this.renderSolvedCategories();
        this.renderGrid();
        this.selectedWords.clear();
        const submitBtn = document.getElementById('submit');
        if (submitBtn) {
            submitBtn.disabled = true;
        }
    }

    handleIncorrectGuess() {
        this.lives--;
        document.getElementById('lives').textContent = this.lives;
        this.showMessage('Not this time buddy, try again!', 'error');

        const grid = document.getElementById('game-grid');
        grid.style.animation = 'none';
        setTimeout(() => (grid.style.animation = 'shake 0.5s ease'), 10);

        if (this.lives <= 0) {
            this.endGame(false);
        }

        this.selectedWords.clear();
        this.renderGrid();
        document.getElementById('submit').disabled = true;
    }

    giveHint() {
        if (this.hintsLeft <= 0) {
            this.showMessage('No more hints for you!', 'error');
            return;
        }

        const unsolvedGroups = this.currentGame.filter(
            (group) => !Array.from(this.solvedGroups).some((solved) => solved.category === group.category),
        );

        if (unsolvedGroups.length > 0) {
            const randomGroup = unsolvedGroups[Math.floor(Math.random() * unsolvedGroups.length)];
            const hint = `Hint: Look for words related to ${randomGroup.category.toLowerCase()}`;
            this.showMessage(hint, 'hint', 6 * 1000);

            this.hintsLeft--;
            document.getElementById('hints-left').textContent = this.hintsLeft;
            document.getElementById('hint').disabled = this.hintsLeft <= 0;
        }
    }

    shuffleGrid() {
        if (!this.gameActive) return;

        const unsolvedWords = this.shuffledWords.filter(
            (word) => !Array.from(this.solvedGroups).some((group) => group.words.includes(word)),
        );

        const shuffledUnsolved = this.shuffle([...unsolvedWords]);
        let index = 0;

        this.shuffledWords = this.shuffledWords.map((word) => {
            if (Array.from(this.solvedGroups).some((group) => group.words.includes(word))) {
                return word;
            }
            return shuffledUnsolved[index++];
        });

        this.selectedWords.clear();
        this.renderGrid();
        document.getElementById('submit').disabled = true;
    }

    showMessage(text, type = 'success', duration = 3000) {
        const container = document.getElementById('toast-container');
        const existing = container.querySelector(`.toast-${type}:not(.toast-hiding)`);
        if (existing) {
            existing.textContent = text;
            clearTimeout(existing._hideTimer);
            existing._hideTimer = setTimeout(() => {
                existing.classList.add('toast-hiding');
                existing.addEventListener('transitionend', () => existing.remove(), { once: true });
            }, parseInt(duration));
            return;
        }
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = text;
        container.appendChild(toast);
        toast._hideTimer = setTimeout(() => {
            toast.classList.add('toast-hiding');
            toast.addEventListener('transitionend', () => toast.remove(), { once: true });
        }, parseInt(duration));
    }

    createConfetti() {
        const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff'];

        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * window.innerWidth + 'px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.animationDelay = Math.random() * 1 + 's';
            document.querySelector('#celebration').appendChild(confetti);

            setTimeout(() => confetti.remove(), 3000);
        }
    }

    startTimer() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        this.startTime = Date.now();
        this.timerInterval = setInterval(() => {
            if (!this.gameActive) return;

            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60)
                .toString()
                .padStart(2, '0');
            const seconds = (elapsed % 60).toString().padStart(2, '0');
            document.getElementById('timer').textContent = `${minutes}:${seconds}`;
        }, 1000);
    }

    endGame(won) {
        this.gameActive = false;
        clearInterval(this.timerInterval);

        const finalTime = document.getElementById('timer').textContent;

        if (won) {
            const gameSet = this.gameSets[this.currentGameIndex];
            const totalRounds = gameSet?.group_sets?.length || 1;
            const nextRound = this.currentRoundIndex + 1;
            const hasNextRound = nextRound < totalRounds;

            this.createConfetti();
            this.saveHighScore(finalTime);

            // Show all categories
            this.currentGame.forEach((group) => {
                if (!Array.from(this.solvedGroups).some((solved) => solved.category === group.category)) {
                    this.solvedGroups.add(group);
                }
            });
            this.renderSolvedCategories();
            this.renderGrid();

            if (hasNextRound) {
                this.showMessage(
                    `Round ${this.currentRoundIndex + 1} done in ${finalTime}! Get ready for Round ${nextRound + 1}...`,
                    'success',
                    4000,
                );
                setTimeout(() => this.startNewGame(this.currentGameIndex, false, nextRound), 4500);
            } else {
                this.showMessage(`Fantastico! You solved them all, and in ${finalTime}!`, 'success');
            }
        } else {
            this.showMessage('Game Over! Better luck next time.', 'error');
        }

        // Disable controls
        document.getElementById('submit').disabled = true;
        document.getElementById('hint').disabled = true;
        document.getElementById('shuffle').disabled = true;

        const gameSet = this.gameSets[this.currentGameIndex];
        const hasNextRound = won && this.currentRoundIndex + 1 < (gameSet?.group_sets?.length || 1);
        if (!hasNextRound) {
            this.showRetryButton();
        }
    }

    showRetryButton() {
        if (!document.getElementById('retry')) {
            const retryButton = document.createElement('button');
            retryButton.id = 'retry';
            retryButton.textContent = 'Play Again?';
            retryButton.className = 'button mdl-button retry-btn';
            retryButton.addEventListener('click', () => {
                document.getElementById('retry').classList.add('hidden');
                this.startNewGame(parseInt(document.getElementById('level-select').value));
            });
            document.getElementById('submit').parentElement.append(retryButton);
        } else {
            document.getElementById('retry').classList.remove('hidden');
        }
        const controls = ['submit', 'hint', 'shuffle', 'reset', 'solve'];
        controls.forEach((id) => {
            const element = document.getElementById(id);
            if (element && !element.classList.contains('hidden')) {
                element.classList.add('hidden');
            }
        });
    }

    saveHighScore(time) {
        const level = parseInt(document.getElementById('level-select').value);
        if (!this.highScores[level] || this.isNewTimeHigher(time, this.highScores[level])) {
            this.highScores[level] = time;
            localStorage.setItem('connectionHighScores', JSON.stringify(this.highScores));
            this.showMessage(`New high score for Game ${level + 1}`, 'success');
        }
    }

    isNewTimeHigher(newTime, oldTime) {
        const [newMin, newSec] = newTime.split(':').map(Number);
        const [oldMin, oldSec] = oldTime.split(':').map(Number);
        return newMin * 60 + newSec < oldMin * 60 + oldSec;
    }

    renderSolvedCategories() {
        const container = document.getElementById('solved-categories');
        Array.from(this.solvedGroups).forEach((group) => {
            const solvedClassColor = `solved-${group.color.toLowerCase()}`;
            const solvedClassColorDot = `.solved-${group.color.toLowerCase()}`;
            if (!container.querySelector(solvedClassColorDot)) {
                const category = document.createElement('div');
                category.className = `category dynamic-item category-solved-focus tooltip ${solvedClassColor}`;
                category.textContent = group.category;
                category.setAttribute('data-tooltip', group?.description || group.category);

                category.setAttribute('solved-color', solvedClassColor.toLowerCase());
                category.addEventListener('mouseover', this.mouseOverHandler);
                category.addEventListener('mouseout', this.mouseOutHandler);
                container.appendChild(category);
            }
        });
    }

    // Game Management Methods
    setupSortableGameSets() {
        const container = document.getElementById('game-sets');

        container.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('game-set')) {
                e.target.classList.add('dragging');
                e.dataTransfer.setData('text/plain', e.target.dataset.index);
            }
        });

        container.addEventListener('dragend', (e) => {
            e.target.classList.remove('dragging');
        });

        container.addEventListener('dragover', (e) => {
            e.preventDefault();
            const draggingEl = document.querySelector('.dragging');
            if (!draggingEl) return;

            const siblings = [...container.querySelectorAll('.game-set:not(.dragging)')];
            const nextSibling = siblings.find((sibling) => {
                const rect = sibling.getBoundingClientRect();
                return e.clientY < rect.top + rect.height / 2;
            });

            container.insertBefore(draggingEl, nextSibling);
        });

        container.addEventListener('drop', (e) => {
            console.log("container.addEventListener('drop')");
            e.preventDefault();
            this.updateGameOrder();
        });
    }

    updateGameOrder() {
        const newOrder = Array.from(document.querySelectorAll('.game-set')).map((el) => parseInt(el.dataset.index));

        this.gameSets = newOrder.map((index) => this.gameSets[index]);
        this.updateGameSets();
        this.setupLevelSelect();

        let lsConfig = JSON.parse(localStorage.getItem('DEFAULT_GAMES'));
        if (lsConfig) {
            lsConfig.game_sets = this.gameSets;
            lsConfig = this.pruneAndUpdateMetadata(lsConfig);
            localStorage.setItem('DEFAULT_GAMES', JSON.stringify(lsConfig));
        }
    }

    updateGameSets() {
        const container = document.getElementById('game-sets');
        container.innerHTML = '';
        const gameObject = this;
        this.gameSets.forEach((game, index) => {
            const setElement = document.createElement('div');
            setElement.className = 'game-set';
            setElement.draggable = true;
            setElement.dataset.index = index;
            let theme = ` - ${game?.theme}` || null;
            const totalRounds = game?.group_sets?.length || 1;
            const roundSuffix = totalRounds > 1 ? ` / ${totalRounds} rounds` : '';
            setElement.innerHTML = `
                            <div class="drag-handle">⋮⋮</div>
                            <div>Game ${index + 1}${roundSuffix} ${theme || ''}</div>
                            <div class="game-set-controls">
                                <button class="button mdl-button edit-btn" onclick="game.openGameEditor(${index})">Edit</button>
                                ${
                                    index >= 1
                                        ? `
                                    <button class="button mdl-button duplicate-btn" onclick="game.duplicateGame(${index})">Duplicate</button>
                                    <button class="button mdl-button delete-btn" onclick="game.removeGameSet(${index})">Delete</button>
                                `
                                        : ''
                                }
                            </div>
                        `;

            container.appendChild(setElement);
        });
    }

    duplicateGame(index) {
        const genId = () => Math.random().toString(16).slice(2, 14).padEnd(12, '0');

        const puzzleCopy = JSON.parse(JSON.stringify(this.gameSets[index]));
        puzzleCopy.game_set_id = genId();
        puzzleCopy.theme = `${puzzleCopy.theme} (copy)`;

        puzzleCopy.group_sets?.forEach((groupSet) => {
            groupSet.forEach?.((group) => {
                group.game_set_id = puzzleCopy.game_set_id;
                group.group_set_id = genId();
                group.group_item_id = genId();
            });
        });

        this.gameSets.push(puzzleCopy);
        this.updateGameSets();
        this.updateGameCount();
        this.setupLevelSelect();

        let lsConfig = JSON.parse(localStorage.getItem('DEFAULT_GAMES'));
        lsConfig.game_sets = this.gameSets;
        lsConfig = this.pruneAndUpdateMetadata(lsConfig);
        localStorage.setItem('DEFAULT_GAMES', JSON.stringify(lsConfig));

        this.showMessage('Game duplicated successfully!', 'success');
    }

    pruneRegistries(data) {
        delete data?.id_registry;
        delete data?.metadata?.id_registry;
        return data;
    }

    pruneAndUpdateMetadata(data) {
        delete data?.id_registry;
        delete data?.metadata?.id_registry;

        const now = new Date().toISOString();
        data.metadata = {
            generated_at: now,
            modified_at: now,
            source: 'DEFAULT_GAMES',
        };

        return data;
    }

    pruneAndSyncRegistries(data) {
        // Collect IDs that actually exist in game_sets
        const liveIds = {
            game_set_ids: new Set(),
            group_set_ids: new Set(),
            group_item_ids: new Set(),
        };

        for (const gameSet of data.game_sets) {
            liveIds.game_set_ids.add(gameSet.game_set_id);

            for (const groupSet of gameSet.group_sets) {
                for (const item of groupSet) {
                    liveIds.group_set_ids.add(item.group_set_id);
                    liveIds.group_item_ids.add(item.group_item_id);
                }
            }
        }

        // Prune a registry object in-place, keeping only live IDs
        const pruneRegistry = (registry) => {
            for (const [key, ids] of Object.entries(registry)) {
                if (Array.isArray(ids) && liveIds[key]) {
                    registry[key] = ids.filter((id) => liveIds[key].has(id));
                }
            }
        };

        if (data.id_registry) pruneRegistry(data.id_registry);
        if (data.metadata?.id_registry) pruneRegistry(data.metadata.id_registry);

        return data;
    }

    removeGameSet(index) {
        if (index >= 0 && index < this.gameSets.length) {
            if (confirm(`Delete this Game - "${this.gameSets[index].theme}"?`)) {
                this.gameSets.splice(index, 1);
                this.updateGameSets();
                this.updateGameCount();
                this.setupLevelSelect();

                const currentLevel = parseInt(document.getElementById('level-select').value);

                let lsConfig = JSON.parse(localStorage.getItem('DEFAULT_GAMES'));
                lsConfig.game_sets = this.gameSets;
                lsConfig = this.pruneAndUpdateMetadata(lsConfig);
                localStorage.setItem('DEFAULT_GAMES', JSON.stringify(lsConfig));

                if (currentLevel >= this.gameSets.length) {
                    this.startNewGame(0);
                }
            }
        }
    }

    expandGameSets() {
        const sets = document.getElementById('game-sets');
        const chevron = document.getElementById('game-sets-chevron');
        sets.classList.remove('game-sets-collapsed');
        chevron.classList.remove('rotated');
    }

    toggleGameSets() {
        const sets = document.getElementById('game-sets');
        const chevron = document.getElementById('game-sets-chevron');
        const collapsed = sets.classList.toggle('game-sets-collapsed');
        chevron.classList.toggle('rotated', collapsed);
    }

    handleFile(file) {
        const isZip = file.type === 'application/zip' || file.name?.endsWith('.zip');
        const isJson = file.type === 'application/json' || file.name?.endsWith('.json');
        if (isZip) {
            this.handleZipFile(file);
            return;
        }
        if (!isJson) {
            this.showMessage('Please upload a JSON or ZIP file', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const gamesTransformed = transformJson(JSON.parse(e.target.result));
                const potentialGames = JSON.parse(JSON.stringify(gamesTransformed));
                console.log(`handleFile: validating`, file.name, potentialGames);
                const validationResult = validateGame(potentialGames);
                console.log(`handleFile: validation result`, validationResult);
                if (validationResult === true) {
                    this.addGameSet(potentialGames);
                    let gameSetsCopy = JSON.parse(JSON.stringify(this.gameSets));
                    let games = JSON.parse(window.localStorage.getItem('DEFAULT_GAMES') || 'null');
                    if (!games) games = { metadata: this.config?.metadata || {}, game_sets: [] };
                    games.game_sets = gameSetsCopy;
                    window.localStorage.setItem('DEFAULT_GAMES', JSON.stringify(games));
                    console.log(`handleFile: saved ${gameSetsCopy.length} game sets to localStorage`);
                    this.showMessage('New Game set loaded successfully!', 'success');
                    setTimeout(() => {
                        this.startNewGame(0);
                    }, 0);
                } else {
                    console.warn(`handleFile: validation failed for ${file.name}:`, validationResult);
                    this.showMessage(`Invalid game file: ${validationResult}`, 'error');
                }
            } catch (error) {
                console.error(`handleFile error for ${file.name}:`, error);
                this.showMessage(`Error parsing file ${error}`, 'error');
            }
        };
        reader.readAsText(file);
    }

    async handleZipFile(file) {
        try {
            const JSZip = require('jszip');
            const zip = await JSZip.loadAsync(file);
            const jsonFiles = Object.values(zip.files).filter((f) => !f.dir && f.name.endsWith('.json'));
            if (jsonFiles.length === 0) {
                this.showMessage('No JSON files found in ZIP', 'error');
                return;
            }
            let loaded = 0;
            for (const zipEntry of jsonFiles) {
                try {
                    const text = await zipEntry.async('string');
                    const gamesTransformed = transformJson(JSON.parse(text));
                    const potentialGames = JSON.parse(JSON.stringify(gamesTransformed));
                    const validationResult = validateGame(potentialGames);
                    if (validationResult === true) {
                        this.addGameSet(potentialGames);
                        loaded++;
                    } else {
                        console.warn(`handleZipFile: skipping ${zipEntry.name}:`, validationResult);
                    }
                } catch (err) {
                    console.warn(`handleZipFile: error processing ${zipEntry.name}:`, err);
                }
            }
            if (loaded > 0) {
                let gameSetsCopy = JSON.parse(JSON.stringify(this.gameSets));
                let games = JSON.parse(window.localStorage.getItem('DEFAULT_GAMES') || 'null');
                if (!games) games = { metadata: this.config?.metadata || {}, game_sets: [] };
                games.game_sets = gameSetsCopy;
                window.localStorage.setItem('DEFAULT_GAMES', JSON.stringify(games));
                this.showMessage(`Loaded ${loaded} game set(s) from ZIP`, 'success');
                setTimeout(() => {
                    this.startNewGame(0);
                }, 0);
            } else {
                this.showMessage('No valid game sets found in ZIP', 'error');
            }
        } catch (error) {
            console.error('handleZipFile error:', error);
            this.showMessage(`Error reading ZIP file: ${error}`, 'error');
        }
    }

    setupLevelSelect() {
        const select = document.getElementById('level-select');
        select.innerHTML = '';

        this.gameSets.forEach((game, index) => {
            const option = document.createElement('option');
            option.value = index;

            // Get high score if it exists
            const highScore = this.highScores[index] || null;
            const highScoreText = highScore ? ` (Best: ${highScore})` : '';

            // Check if it's a custom game
            const customText = index >= DEFAULT_GAMES_SET_COUNT ? ' (Custom)' : '';

            // Create the option text
            const themeText = game?.theme ? ` - ${game.theme}` : '';
            const totalRounds = game?.group_sets?.length || 1;
            const roundText = totalRounds > 1 ? ` (${totalRounds} rounds)` : '';
            option.textContent = `Game ${index + 1}${themeText}${roundText}${customText}${highScoreText}`;

            // If this is the current level, select it
            if (this.currentGame && this.game_set_id === this.gameSets[index].game_set_id) {
                option.selected = true;
            }

            select.appendChild(option);
        });

        // Add event listener if not already added in constructor
        if (!this.levelSelectInitialized) {
            select.addEventListener('change', (e) => {
                const newLevel = parseInt(e.target.value);
                this.startNewGame(newLevel);
            });
            this.levelSelectInitialized = true;
        }

        // Update the select styling based on custom/default status
        this.updateLevelSelectStyling();
    }

    updateLevelSelectStyling() {
        const select = document.getElementById('level-select');

        // Style for the select element
        select.style.padding = '8px 12px';
        select.style.borderRadius = '6px';
        select.style.border = '1px solid #e2e8f0';
        select.style.fontSize = '0.875rem';
        select.style.backgroundColor = 'white';
        select.style.cursor = 'pointer';
        select.style.minWidth = '200px';

        // Style options within the select
        Array.from(select.options).forEach((option, index) => {
            if (index >= DEFAULT_GAMES_SET_COUNT) {
                option.style.backgroundColor = '#f8fafc'; // Light gray for custom puzzles
                option.style.fontStyle = 'italic';
            }

            // Add high score styling if exists
            if (this.highScores[index]) {
                option.style.fontWeight = '500';
            }
        });

        // Create a wrapper div for better styling if it doesn't exist
        let wrapper = select.parentElement;
        if (!wrapper.classList.contains('level-select-wrapper')) {
            wrapper = document.createElement('div');
            wrapper.className = 'level-select-wrapper';
            wrapper.style.display = 'flex';
            wrapper.style.alignItems = 'center';
            wrapper.style.gap = '10px';
            wrapper.style.justifyContent = 'center';
            wrapper.style.margin = '20px 0';

            // Add label
            const label = document.createElement('label');
            label.textContent = 'Level:';
            label.style.fontWeight = '500';
            label.style.color = '#4b5563';

            // Move select into wrapper
            select.parentElement.insertBefore(wrapper, select);
            wrapper.appendChild(label);
            wrapper.appendChild(select);
        }

        // Add hover effect
        select.addEventListener('mouseover', () => {
            select.style.borderColor = '#cbd5e1';
        });

        select.addEventListener('mouseout', () => {
            select.style.borderColor = '#e2e8f0';
        });

        // Add focus styling
        select.addEventListener('focus', () => {
            select.style.outline = 'none';
            select.style.borderColor = '#3b82f6';
            select.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
        });

        select.addEventListener('blur', () => {
            select.style.borderColor = '#e2e8f0';
            select.style.boxShadow = 'none';
        });
    }

    async exportGames() {
        const JSZip = require('jszip');
        const DEFAULT_GAMES = JSON.parse(window.localStorage.getItem('DEFAULT_GAMES'));
        const gameSets = DEFAULT_GAMES?.game_sets ?? [];
        const dateStamp = new Date().toISOString().slice(0, 10);

        const saveWithPicker = async (blob, suggestedName, mimeType, ext) => {
            if ('showSaveFilePicker' in window) {
                try {
                    const handle = await window.showSaveFilePicker({
                        suggestedName,
                        startIn: 'downloads',
                        types: [{ description: ext.toUpperCase() + ' file', accept: { [mimeType]: ['.' + ext] } }],
                    });
                    const writable = await handle.createWritable();
                    await writable.write(blob);
                    await writable.close();
                    return;
                } catch (e) {
                    if (e.name === 'AbortError') return; // user cancelled
                    // fall through to legacy download
                }
            }
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = suggestedName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        };

        if (gameSets.length <= 1) {
            const toUrlSlug = (str) =>
                (str ?? '')
                    .toLowerCase()
                    .replace(/[^a-z0-9]+/g, '-')
                    .replace(/^-|-$/g, '');
            const gameSet = gameSets[0];
            const id = gameSet?.game_set_id ?? 'find4-games';
            const theme = gameSet?.theme ?? gameSet?.group_sets?.[0]?.[0]?.theme;
            const slug = theme
                ? toUrlSlug(theme)
                : toUrlSlug(DEFAULT_GAMES?.metadata?.suggested_name?.replace(/\.json$/, '') ?? '');
            const content = JSON.stringify(DEFAULT_GAMES, null, 2);
            const zip = new JSZip();
            const folder = zip.folder(`export/find4_${dateStamp}_export`);
            folder.file(`${dateStamp}_${id}.json`, content);
            if (slug && slug !== id) {
                folder.file(`${dateStamp}_${slug}.json`, content);
            }
            const zipBlob = await zip.generateAsync({ type: 'blob' });
            await saveWithPicker(zipBlob, `find4_${dateStamp}_${slug || id}.zip`, 'application/zip', 'zip');
        } else {
            const zip = new JSZip();
            const folder = zip.folder(`export/find4_${dateStamp}_export`);
            const toUrlSlug = (str) =>
                (str ?? '')
                    .toLowerCase()
                    .replace(/[^a-z0-9]+/g, '-')
                    .replace(/^-|-$/g, '');
            gameSets.forEach((gameSet) => {
                const id = gameSet.game_set_id ?? `game_${Date.now()}`;
                const content = JSON.stringify(gameSet, null, 2);
                folder.file(`${dateStamp}_${id}.json`, content);
                const theme = gameSet.theme ?? gameSet.group_sets?.[0]?.[0]?.theme;
                if (theme) {
                    folder.file(`${dateStamp}_${toUrlSlug(theme)}.json`, content);
                }
            });
            const zipBlob = await zip.generateAsync({ type: 'blob' });
            await saveWithPicker(zipBlob, `find4_${dateStamp}_export.zip`, 'application/zip', 'zip');
        }
    }

    closeEditor() {
        this.modalManager.hideModal('editor-modal');
        document.getElementById('editor-modal').classList.remove('visible');
        document.getElementById('editor-validation').textContent = '';
    }

    addGameSet(gameDataToAdd) {
        // Create a map of new items by game_set_id
        let gameData = null;
        if (gameDataToAdd?.metadata && gameDataToAdd?.game_sets) {
            gameData = gameDataToAdd.game_sets;
        } else {
            gameData = gameDataToAdd;
        }
        const newSetsMap = new Map(gameData.map((set) => [set.game_set_id, set]));
        // Update existing or add new games
        this.gameSets = this.gameSets.map((existingSet) =>
            newSetsMap.has(existingSet.game_set_id) ? newSetsMap.get(existingSet.game_set_id) : existingSet,
        );

        // Prepend any completely new items so newly loaded games appear first
        const trulyNew = gameData.filter(
            (newSet) => !this.gameSets.some((set) => set.game_set_id === newSet.game_set_id),
        );
        this.gameSets = [...trulyNew, ...this.gameSets];

        this.updateGameSets();
        this.updateGameCount();
        this.setupLevelSelect();
    }
    saveGame() {
        if (this.gameManager.editingIndex === null) {
            const genId = () => Math.random().toString(16).slice(2, 14).padEnd(12, '0');
            const newId = genId();
            this.gameSets.push({ game_set_id: newId, theme: '', group_sets: [[]] });
            this.gameManager.editingIndex = this.gameSets.length - 1;
        }
        const gameDataFromEditor = this.gameManager.getEditorData();

        const gameData = gameDataFromEditor.groups;
        const groupTheme = gameDataFromEditor.groupThemeName;

        // const validationResult = validateGame({ groups: gameData });

        // if (!(validationResult == true)) {
        //     document.getElementById('editor-validation').textContent = validationResult;
        //     return;
        // }

        this.gameSets[this.gameManager.editingIndex].theme = groupTheme;

        let existingGamedata = this.gameSets[this.gameManager.editingIndex].group_sets[0];
        let mergedGameData = mergeObjectArrays(existingGamedata, gameData);

        let gameSetsCopy = JSON.parse(JSON.stringify(this.gameSets));

        gameSetsCopy[this.gameManager.editingIndex].group_sets[0] = mergedGameData;
        const validationResult = validateGame(gameSetsCopy);
        if (validationResult === true) {
            this.gameSets = gameSetsCopy;
            if (window.localStorage.getItem('DEFAULT_GAMES')) {
                let games = JSON.parse(window.localStorage.getItem('DEFAULT_GAMES'));
                if (games?.metadata && games?.game_sets) {
                    games.game_sets = gameSetsCopy;
                    window.localStorage.setItem('DEFAULT_GAMES', JSON.stringify(games));
                }
            }
        } else {
            this.gameSets.pop();
            this.gameManager.editingIndex = null;
            this.showMessage(`Validation failed: ${validationResult}`, 'error');
            return;
        }

        this.closeEditor();
        this.updateGameSets();
        this.setupLevelSelect();
        this.updateGameCount();
        this.renderGrid();
        if (this.gameManager.editingIndex !== null) {
            this.startNewGame(this.gameManager.editingIndex);
        }
        this.showMessage('Game(s) saved successfully!', 'success');
    }

    updateGameCount() {
        document.getElementById('puzzle-count').textContent = this.gameSets.length;
    }
}

// Orientation/repaint handling — currently disabled. Keeping the logic here because
// I'll likely want it once I tackle the mobile layout properly.
const setupOrientation = () => {
    return;
    const repaint = () => {
        const element = document.querySelector('body');
        ((element) => {
            // Toggle a class to force a repaint
            element.classList.add('force-repaint');
            requestAnimationFrame(() => {
                element.classList.remove('force-repaint');
            });

            // Alternatively, change a style property
            element.style.display = 'none';
            element.offsetHeight; // Force a reflow
            element.style.display = '';

            // Or using transform property
            element.style.transform = 'scale(1)';
            requestAnimationFrame(() => {
                element.style.transform = '';
            });
        })(element);
    };
    (function () {
        // Function to handle orientation changes
        function handleOrientationChange() {
            const width = window.innerWidth;
            const height = window.innerHeight;
            const isLandscape = width > height;

            // Get root element to update
            const root = document.documentElement;

            // Update CSS custom properties for dimensions
            root.style.setProperty('--window-width', `${width}px`);
            root.style.setProperty('--window-height', `${height}px`);

            // Update orientation class on body
            document.body.classList.toggle('landscape', isLandscape);
            document.body.classList.toggle('portrait', !isLandscape);

            // Dispatch custom event
            const event = new CustomEvent('orientationChanged', {
                detail: {
                    isLandscape,
                    width,
                    height,
                    orientation: isLandscape ? 'landscape' : 'portrait',
                    angle: window.orientation || 0,
                },
            });
            window.dispatchEvent(event);
        }

        // Add event listeners
        window.addEventListener('resize', repaint);
        window.addEventListener('orientationchange', repaint);
        // window.addEventListener('resize', handleOrientationChange);
        // window.addEventListener('orientationchange', handleOrientationChange);

        // Initial call
        handleOrientationChange();

        // Example usage:
        window.addEventListener('orientationChanged', (e) => {
            console.log('Orientation:', e.detail.orientation);
            console.log('Dimensions:', e.detail.width, 'x', e.detail.height);
        });
    })();
};

// Field order must match SHARE_SCHEMA in share_game.sh
const SHARE_SCHEMA = ['words', 'category', 'color', 'group_item_id', 'group_set_id'];

const expandCompactGame = (compact) => ({
    game_sets: compact.game_sets.map((gs) => ({
        theme: gs.theme,
        game_set_id: gs.game_set_id,
        group_sets: gs.group_sets.map((groupSet) =>
            groupSet.map((row) => Object.fromEntries(SHARE_SCHEMA.map((key, i) => [key, row[i]]))),
        ),
    })),
});

// Hydrate a game produced by add_ids.py --flatten: groups are value arrays keyed by root schema.
const hydratePackedGame = (data) => {
    if (!Array.isArray(data.schema)) return data;
    const schema = data.schema;
    return {
        ...data,
        game_sets: data.game_sets.map((gs) => ({
            ...gs,
            group_sets: gs.group_sets.map((groupSet) =>
                groupSet.map((row) =>
                    Array.isArray(row) ? Object.fromEntries(schema.map((key, i) => [key, row[i]])) : row,
                ),
            ),
        })),
    };
};

const loadGameFromUrl = async () => {
    const hash = window.location.hash; // e.g. "#game=eyJtZXRhZG..."
    if (!hash.startsWith('#game=')) return null;

    try {
        const encoded = hash.slice('#game='.length);
        // Restore padding stripped by Python's urlsafe_b64encode, then convert to standard base64 for atob
        const padded = encoded + '='.repeat((4 - (encoded.length % 4)) % 4);
        const standard = padded.replace(/-/g, '+').replace(/_/g, '/');
        const bytes = Uint8Array.from(atob(standard), (c) => c.charCodeAt(0));

        // Try zlib-compressed payload first, fall back to plain JSON (old format)
        let parsed;
        try {
            const ds = new DecompressionStream('deflate-raw');
            const decompressedStream = new Blob([bytes]).stream().pipeThrough(ds);
            const decompressedBuffer = await new Response(decompressedStream).arrayBuffer();
            parsed = JSON.parse(new TextDecoder().decode(decompressedBuffer));
        } catch (e) {
            console.warn('Decompression failed, attempting raw parse:', e);
            parsed = JSON.parse(new TextDecoder().decode(bytes));
        }

        // v2 compact format: arrays instead of objects in group_sets
        if (parsed?.v === 2) return expandCompactGame(parsed);
        // add_ids.py --flatten: groups packed as value arrays with root schema key
        if (parsed?.schema) return hydratePackedGame(parsed);
        return parsed;
    } catch (e) {
        console.error('Failed to decode game from URL:', e);
        return null;
    }
};

// allow some options to be passed in via the url params
const parseURLParams = () => {
    // Create a global object to store params
    window.urlParams = new Map();

    // Get the current URL's search params (everything after ?)
    const searchParams = window.location.search;

    // If no search params exist, return empty object
    if (!searchParams) return window.urlParams;

    // Remove the leading ? and split into key-value pairs
    const params = searchParams.substring(1).split('&');

    // Create temporary map of Sets to store unique values
    const paramSets = new Map();

    // Process each key-value pair
    params.forEach((param) => {
        // Split into key and value
        const [key, value] = param.split('=');

        // Decode the key and value to handle special characters
        const decodedKey = decodeURIComponent(key);
        const decodedValue = decodeURIComponent(value || '');

        // Get or create Set for this key
        if (!paramSets.has(decodedKey)) {
            paramSets.set(decodedKey, new Set());
        }

        // Add value to Set (automatically handles uniqueness)
        paramSets.get(decodedKey).add(decodedValue);
    });

    // Convert Sets to either single values or arrays
    paramSets.forEach((valueSet, key) => {
        const values = Array.from(valueSet);
        window.urlParams[key] = values.length === 1 ? values[0] : values;
        if (!window.urlParams.has(key)) {
            window.urlParams.set(key, null);
        }
        window.urlParams.set(key, values.length === 1 ? values[0] : values);
    });

    return window.urlParams;
};

// App main entry point. I've not made this responsive in any way for now
document.addEventListener('DOMContentLoaded', async () => {
    const DEF = [
        {
            groups: [
                {
                    words: ['RATE', 'DURATION', 'REQUESTS', 'LATENCY'],
                    category: 'RED Method',
                    color: 'red',
                    url: 'https://www.splunk.com/en_us/blog/learn/red-monitoring.html',
                },
                {
                    words: ['UTILIZATION', 'SATURATION', 'RESOURCES', 'QUEUE'],
                    category: 'USE Method',
                    color: 'blue',
                    url: 'https://sre.google/sre-book/service-level-objectives/',
                },
                {
                    words: ['DELAY', 'NOISE', 'CROSSTALK', 'INTERFERENCE'],
                    category: 'DUNE Method',
                    color: 'green',
                    url: 'https://sre.google/sre-book/service-level-objectives/',
                },
                {
                    words: ['DOWNSTREAM', 'UPTIME', 'STALENESS', 'DEPENDENCIES'],
                    category: 'DURESS Method',
                    color: 'purple',
                    url: 'https://sre.google/sre-book/service-level-objectives/',
                },
            ],
        },
    ];

    try {
        const initGame = async (initResult) => {
            // 1. localStorage takes priority — user's saved/imported games

            // On startup — URL-encoded game takes highest priority
            const urlGames = await loadGameFromUrl();
            if (urlGames?.game_sets?.length > 0) {
                console.info(`Loading ${urlGames.game_sets.length} game(s) from URL`);

                //history.replaceState(null, '', window.location.pathname + window.location.search);

                window.localStorage.setItem('URL_HASH_GAMES', JSON.stringify(urlGames));
                DEFAULT_GAMES = urlGames;
                const game = new ConnectionsGame(DEFAULT_GAMES);
                return game;
            }

            const urlHashStored = window.localStorage.getItem('URL_HASH_GAMES');
            if (urlHashStored && !urlParams?.config) {
                try {
                    const urlHashGames = JSON.parse(urlHashStored);
                    if (urlHashGames?.game_sets?.length > 0) {
                        console.info(`Restoring ${urlHashGames.game_sets.length} game(s) from URL_HASH_GAMES`);
                        DEFAULT_GAMES = urlHashGames;
                        const game = new ConnectionsGame(DEFAULT_GAMES);
                        return game;
                    }
                } catch (e) {
                    console.warn('URL_HASH_GAMES parse failed, falling through:', e.message);
                }
            }

            const stored = !urlParams?.config && window.localStorage.getItem('DEFAULT_GAMES');
            if (stored) {
                try {
                    const storedGames = JSON.parse(stored);
                    if (storedGames?.game_sets?.length > 0) {
                        console.info(`Restoring ${storedGames.game_sets.length} game(s) from localStorage`);
                        DEFAULT_GAMES = storedGames;
                        const game = new ConnectionsGame(DEFAULT_GAMES);

                        // When ?config= is explicit, merge the remote game set to the front
                        const hasRemoteConfig =
                            initResult?.success === true &&
                            initResult?.config &&
                            typeof initResult.config === 'object' &&
                            Object.keys(initResult.config).length > 0;

                        if (hasRemoteConfig && urlParams?.config) {
                            const gamesTransformed = transformJson(initResult.config);
                            const potentialGames = JSON.parse(JSON.stringify(gamesTransformed));
                            const validatedGames = validateGame(potentialGames);
                            if (validatedGames === true) {
                                console.info('Prepending remote config game set(s) from ?config= URL');
                                game.addGameSet(potentialGames);
                                const updatedGames =
                                    JSON.parse(window.localStorage.getItem('DEFAULT_GAMES') || 'null') || DEFAULT_GAMES;
                                updatedGames.game_sets = game.gameSets;
                                window.localStorage.setItem('DEFAULT_GAMES', JSON.stringify(updatedGames));
                                game.startNewGame(0);
                            }
                        }

                        return game;
                    }
                } catch (e) {
                    console.warn('localStorage parse failed, falling through:', e.message);
                }
            }

            // 2. Remote config — only used when localStorage is empty/invalid
            const hasConfig =
                initResult?.success === true &&
                initResult?.config &&
                typeof initResult.config === 'object' &&
                Object.keys(initResult.config).length > 0;

            if (!hasConfig) {
                console.warn('No valid config loaded. Starting with default games.');
            } else {
                let gamesTransformed = transformJson(initResult.config);
                let potentialGames = JSON.parse(JSON.stringify(gamesTransformed));

                const validatedGames = validateGame(potentialGames);
                if (validatedGames === true) {
                    DEFAULT_GAMES = stampMetadataFingerprint(potentialGames);
                    window.localStorage.setItem('DEFAULT_GAMES', JSON.stringify(DEFAULT_GAMES));
                    console.info('Loaded remote config and saved to localStorage');
                }
            }

            // 3. Hardcoded DEFAULT_GAMES is the final fallback
            const game = new ConnectionsGame(DEFAULT_GAMES);
            return game;
        };

        //setupOrientation();
        const urlParams = parseURLParams();

        const shortLinkMatch = window.location.pathname.match(/^\/l\/([^/]+)$/);
        if (shortLinkMatch) {
            const slug = shortLinkMatch[1];
            const candidateUrl = `/library/${slug}/${slug}.json`;
            const probe = await fetch(candidateUrl, { method: 'HEAD' });
            if (probe.ok) {
                const base = window.location.origin;
                const newUrl = `${base}/index.html?config=${base}${candidateUrl}`;
                window.location.replace(newUrl);
                return;
            }
            console.warn(`Short link /l/${slug} -> ${candidateUrl} not found (${probe.status})`);
        }

        const ffParam = window.location.search.match(/^\?ff-([0-9a-f]{8})$/);
        if (ffParam) {
            const incoming = `ff-${ffParam[1]}`;
            try {
                const resp = await fetch(`/library/themes.json?_t=${Date.now()}`);
                if (resp.ok) {
                    const themes = await resp.json();
                    for (const t of themes) {
                        const code = ffHash(t.short_path);
                        if (code === incoming) {
                            const base = window.location.origin;
                            console.log(`redirecting [${code}] to ${base}/${t.short_path}`);

                            window.location.replace(`${base}/index.html?config=${t.short_path}`);
                            // window.location.replace(`${base}/index.html?config=${base}/${t.short_path}`);

                            return;
                        }
                    }
                }
            } catch (e) {
                console.warn('ff-link resolution failed:', e.message);
            }
            console.warn(`ff-link ${incoming} did not match any theme in themes.json`);
        }

        const savedSource = localStorage.getItem('GAME_SOURCE') || 'default';
        let sourceConfigUrl = savedSource === 'library' ? '/library/library.json' : '/config/default.json';
        if (savedSource === 'default' && !urlParams?.config) {
            try {
                const probe = await fetch(sourceConfigUrl, { method: 'HEAD' });
                if (!probe.ok) {
                    console.log(`${sourceConfigUrl} not found (${probe.status}), using library/themes.json`);
                    sourceConfigUrl = 'library/themes.json';
                }
            } catch (e) {
                console.log(`${sourceConfigUrl} unreachable, using library/themes.json`);
                sourceConfigUrl = 'library/themes.json';
            }
        }
        const config_url = urlParams?.config || sourceConfigUrl;
        console.log(`getting initial config from ${config_url} (source: ${savedSource})`);
        const loadedConfig = await loadConfig({ url: config_url });
        window.game = await initGame(loadedConfig.success ? loadedConfig : { success: false, config: null });
        if (window.game.detector.isMobile()) {
            console.log('ismobile is true');
            document.querySelector('.shift-btn').classList.remove('hidden');
        }
        window.game.showMessage('Find4 is ready. See the Help for game mechanics', 'success', 5000);
    } catch (error) {
        console.error('Find4 startup failed:', error);
    }
});
