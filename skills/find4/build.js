const esbuild = require('esbuild');
const glob = require('glob');
const JavaScriptObfuscator = require('javascript-obfuscator');
const fs = require('fs');
const fsp = require('fs').promises;
const path = require('path');

// Parse command line arguments
const args = process.argv.slice(2);
const cliArgs = {};
args.forEach((arg) => {
    if (arg.startsWith('--')) {
        const [key, value] = arg.slice(2).split('=');
        cliArgs[key] = value === 'false' ? false : value === 'true' ? true : value;
    }
});

// Read configuration from package.json
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const buildConfig = packageJson.buildConfig || {};

// Default configuration, overridden by package.json, then by CLI arguments
const config = {
    bundle: true,
    minify: true,
    obfuscate: true,
    ...buildConfig,
    ...cliArgs,
};

console.log('Build configuration:', config);

// Obfuscation options
const obfuscationOptions = {
    compact: true,
    controlFlowFlattening: true,
    controlFlowFlatteningThreshold: 0.75,
    deadCodeInjection: true,
    deadCodeInjectionThreshold: 0.4,
    debugProtection: false,
    debugProtectionInterval: 2000,
    disableConsoleOutput: true,
    identifierNamesGenerator: 'hexadecimal',
    renameGlobals: false,
    rotateStringArray: true,
    selfDefending: true,
    shuffleStringArray: true,
    splitStrings: true,
    splitStringsChunkLength: 10,
    stringArray: true,
    stringArrayEncoding: ['base64'],
    stringArrayThreshold: 0.75,
    transformObjectKeys: true,
    unicodeEscapeSequence: false,
};

/**
 * Copies build files to standardized bundle names
 * @param {Object} buildResult - The esbuild result object
 * @param {string} sourceFile - Original source file name (e.g., 'static/js/MainApp.js')
 * @param {string} type - File type ('js' or 'css')
 */
async function copyToBundleName(buildResult, sourceFile, type) {
    try {
        if (!buildResult?.metafile?.outputs) {
            throw new Error(`Invalid build result for ${type}`);
        }

        // Get the output file path from build result
        const outputFiles = Object.keys(buildResult.metafile.outputs);

        if (outputFiles.length === 0) {
            throw new Error(`No output files found for ${type}`);
        }

        console.log(`Available output files for ${type}:`, outputFiles);

        const sourceBaseName = path.basename(sourceFile);

        // Find the corresponding output file
        const outputFile = outputFiles.find((file) => file.includes(sourceBaseName) || file.endsWith(`.${type}`));

        if (!outputFile) {
            throw new Error(`Could not find output file for ${sourceFile} in ${outputFiles.join(', ')}`);
        }

        // Verify source file exists
        try {
            await fsp.access(outputFile);
        } catch (error) {
            throw new Error(`Output file ${outputFile} does not exist or is not accessible`);
        }

        // Create dist directory if it doesn't exist
        const distDir = 'dist';
        try {
            await fsp.access(distDir);
        } catch {
            await fsp.mkdir(distDir, { recursive: true });
            console.log('Created dist directory');
        }

        // Define standard bundle names
        const standardNames = {
            js: 'bundle.min.js',
            css: 'bundle.min.css',
        };

        const targetFile = path.join(distDir, standardNames[type]);

        // Copy the file
        await fsp.copyFile(outputFile, targetFile);
        console.log(`Copied ${outputFile} to ${targetFile}`);

        // Verify target file exists and get size
        try {
            const stats = await fsp.stat(targetFile);
            if (stats && stats.size !== undefined) {
                console.log(`${targetFile} size: ${Math.round(stats.size / 1024)}KB`);
            } else {
                console.log(`Warning: Could not get size for ${targetFile}`);
            }
        } catch (error) {
            console.error(`Warning: Error getting file size for ${targetFile}:`, error);
        }
    } catch (error) {
        console.error(`Error in copyToBundleName for ${type}:`);
        console.error('Error details:', error);
        console.error('Build result structure:', JSON.stringify(buildResult, null, 2));
        throw error;
    }
}
// Function to obfuscate a file
const obfuscateFile = async (filePath) => {
    const code = fs.readFileSync(filePath, 'utf8');
    const obfuscationResult = JavaScriptObfuscator.obfuscate(code, obfuscationOptions);
    fs.writeFileSync(filePath, obfuscationResult.getObfuscatedCode());
    console.log(`Obfuscated: ${filePath}`);
};

// Common build options
const getBaseBuildOptions = (entryPoint) => ({
    entryPoints: [entryPoint],
    outdir: 'dist',
    bundle: config.bundle,
    minify: config.minify,
    sourcemap: false,
    write: true,
    treeShaking: true,
    platform: 'browser',
    metafile: true,
});

// Show help message if requested
if (cliArgs.help || cliArgs.h) {
    console.log(`
Usage: node build.js [options]

Options:
    --bundle=boolean    Enable/disable bundling (default: true)
    --minify=boolean    Enable/disable minification (default: true)
    --obfuscate=boolean Enable/disable obfuscation (default: true)
    --help, -h         Show this help message

Examples:
    node build.js --minify=false
    node build.js --bundle=false --obfuscate=false
    node build.js --help
    `);
    process.exit(0);
}

// Build and optionally obfuscate
Promise.all([
    // Build JavaScript
    esbuild.build({
        ...getBaseBuildOptions('js/find4.js'),
        format: 'iife',
        target: ['es6'],
        loader: { '.js': 'js' },
    }),

    // Build CSS
    esbuild.build({
        ...getBaseBuildOptions('css/find4.css'),
        loader: { '.css': 'css' },
    }),
])
    .then(async ([jsResult, cssResult]) => {
        console.log('Build complete. ', jsResult, cssResult);
        try {
            // Copy files to standard names
            await Promise.all([
                copyToBundleName(jsResult, 'js/find4.js', 'js'),
                copyToBundleName(cssResult, 'css/find4.css', 'css'),
            ]);

            console.log('File copying completed successfully');
        } catch (error) {
            console.error('Error during file copying:', error);
            process.exit(1);
        }

        if (config.obfuscate) {
            console.log('Starting obfuscation...');
            // Obfuscate all generated JS files
            const jsFiles = Object.keys(jsResult.metafile.outputs).filter((file) => file.endsWith('.js'));

            for (const file of jsFiles) {
                await obfuscateFile(file);
            }
        }

        // Log final bundle sizes
        const logFileSize = (file) => {
            const stats = fs.statSync(file);
            console.log(`${file}: ${Math.round(stats.size / 1024)}KB`);
        };

        const jsFiles = Object.keys(jsResult.metafile.outputs).filter((file) => file.endsWith('.js'));
        const cssFiles = Object.keys(cssResult.metafile.outputs).filter((file) => file.endsWith('.css'));

        console.log('\nFinal bundle sizes:');
        jsFiles.forEach(logFileSize);
        cssFiles.forEach(logFileSize);
    })
    .catch((error) => {
        console.error('Build failed:', error);
        process.exit(1);
    });
