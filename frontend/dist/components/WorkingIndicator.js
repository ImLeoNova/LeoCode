import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { Box, Text } from 'ink';
import { theme } from '../styles/theme.js';
const WORKING_PHRASES = [
    'Mining diamonds...',
    'Untangling spaghetti...',
    'Consulting the AI gods...',
    'Summoning the neurons...',
    'Teaching pixels to think...',
    'Shuffling some electrons...',
    'Asking the rubber duck...',
    'Negotiating with the compiler...',
    'Counting imaginary bytes...',
    'Polishing the neural network...',
    'Herding tokens...',
    'Chasing a runaway semicolon...',
    'Feeding the AI hamster...',
    'Searching the void...',
    'Connecting the brain cells...',
    'Convincing the code to work...',
    'Sacrificing a few electrons...',
    'Brewing some algorithms...',
    'Waking up the neurons...',
    'Untangling the code noodles...',
    'Compressing the chaos...',
    'Fighting the bugs...',
    'Negotiating with reality...',
    'Loading suspicious amounts of intelligence...',
    'Summoning forbidden knowledge...',
    'Looking under the digital couch...',
    'Asking the silicon oracle...',
    'Turning coffee into code...',
    'Aligning the semicolons...',
    'Hunting for missing brackets...',
    'Performing computational wizardry...',
    'Recalculating everything...',
    'Making the electrons behave...',
    'Inspecting the matrix...',
    'Searching for the last bug...',
    'Convincing the CPU this was intentional...',
    'Counting tokens...',
    'Rearranging the digital furniture...',
    'Doing suspiciously intelligent things...',
    'Thinking at approximately light speed...',
    'Making questionable architectural decisions...',
    'Turning chaos into code...',
    'Negotiating with the garbage collector...',
    'Bribing the compiler...',
    'Looking for the good timeline...',
    'Consulting ancient documentation...',
    'Searching Stack Overflow spiritually...',
    'Asking nicely for the code to work...',
    'Removing the invisible bug...',
    'Deploying brain.exe...',
    'Initializing questionable genius...',
    'Generating excessive amounts of computation...',
    'Checking if it works on my machine...',
    'Summoning more RAM...',
    'Digging through the codebase...',
    'Following the suspicious function...',
    'Hunting down that one weird edge case...',
    'Making the terminal nervous...',
    'Calculating absolutely everything...',
    'Teaching the code some manners...',
    'Turning thoughts into tokens...',
];
const SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
const PHRASE_INTERVAL_MS = 3000;
const SPINNER_INTERVAL_MS = 80;
export const WorkingIndicator = () => {
    const [phraseIndex, setPhraseIndex] = useState(() => Math.floor(Math.random() * WORKING_PHRASES.length));
    const [spinnerFrame, setSpinnerFrame] = useState(0);
    useEffect(() => {
        const phraseTimer = setInterval(() => {
            setPhraseIndex(prev => (prev + 1) % WORKING_PHRASES.length);
        }, PHRASE_INTERVAL_MS);
        const spinnerTimer = setInterval(() => {
            setSpinnerFrame(prev => (prev + 1) % SPINNER_FRAMES.length);
        }, SPINNER_INTERVAL_MS);
        return () => {
            clearInterval(phraseTimer);
            clearInterval(spinnerTimer);
        };
    }, []);
    const spinner = SPINNER_FRAMES[spinnerFrame];
    const phrase = WORKING_PHRASES[phraseIndex];
    return (_jsxs(Box, { paddingLeft: 1, children: [_jsx(Text, { color: theme.status.processing, bold: true, children: spinner }), _jsxs(Text, { color: theme.fg.muted, children: [' ', phrase] })] }));
};
//# sourceMappingURL=WorkingIndicator.js.map