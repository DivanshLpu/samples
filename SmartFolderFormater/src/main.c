#define WIN32_LEAN_AND_MEAN
#define _CRT_SECURE_NO_WARNINGS

#include <windows.h>
#include <shlobj.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define APP_NAME "Smart File Organizer"
#define CLASS_NAME "SmartFileOrganizerClass"
#define MAX_FILES 10000
#define MAX_PATH_LEN 4096
#define ID_FOLDER_EDIT 1001
#define ID_BROWSE 1002
#define ID_SCAN 1003
#define ID_ORGANIZE 1004
#define ID_UNDO 1005
#define ID_LIST 1006
#define ID_STATUS 1007
#define ID_TOTAL 1008
#define ID_IMAGES 1009
#define ID_DOCUMENTS 1010
#define ID_VIDEOS 1011
#define ID_AUDIO 1012
#define ID_ARCHIVES 1013
#define ID_PROGRAMS 1014
#define ID_OTHER 1015
#define ID_BATCH_BASE 50000

#define CLR_BG RGB(245,247,250)
#define CLR_HEADER RGB(35,42,52)
#define CLR_TEXT RGB(35,35,35)
#define CLR_MUTED RGB(100,105,112)
#define CLR_BLUE RGB(55,105,210)
#define CLR_GREEN RGB(45,155,90)

#ifdef _MSC_VER
#pragma comment(lib, "shell32.lib")
#endif

typedef enum {
    CAT_IMAGES,
    CAT_DOCUMENTS,
    CAT_VIDEOS,
    CAT_AUDIO,
    CAT_ARCHIVES,
    CAT_PROGRAMS,
    CAT_OTHER,
    CAT_COUNT
} Category;

typedef struct {
    char name[MAX_PATH];
    char source[MAX_PATH_LEN];
    Category category;
} FileItem;

typedef struct {
    char source[MAX_PATH_LEN];
    char destination[MAX_PATH_LEN];
} HistoryEntry;

typedef struct {
    HWND hwnd;
    HWND folderEdit;
    HWND fileList;
    HWND status;
    HWND counts[CAT_COUNT];
    HWND total;
    HFONT normalFont;
    HFONT boldFont;
    HFONT titleFont;
} App;

static App app;
static FileItem files[MAX_FILES];
static int fileCount = 0;
static int categoryCounts[CAT_COUNT] = {0};
static unsigned long long currentBatchId = 0;

static const char *categoryNames[CAT_COUNT] = {
    "Images", "Documents", "Videos", "Audio", "Archives", "Programs", "Other"
};

static void scanFolder(void);
static void organizeFiles(void);
static void undoLastBatch(void);
static void setStatusText(const char *text);

static void safe_copy(char *dst, size_t dstSize, const char *src) {
    if (dstSize == 0) return;
    strncpy(dst, src ? src : "", dstSize - 1);
    dst[dstSize - 1] = '\0';
}

static void join_path(char *out, size_t outSize, const char *a, const char *b) {
    if (!a || !b) { if (outSize) out[0] = '\0'; return; }
    snprintf(out, outSize, "%s%s%s", a,
             (a[0] && a[strlen(a)-1] != '\\' && a[strlen(a)-1] != '/') ? "\\" : "", b);
}

static int is_directory(const char *path) {
    DWORD attr = GetFileAttributesA(path);
    return attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_DIRECTORY);
}

static int is_regular_file(const char *path) {
    DWORD attr = GetFileAttributesA(path);
    return attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY);
}

static int ensure_directory(const char *path) {
    if (is_directory(path)) return 1;
    if (CreateDirectoryA(path, NULL)) return 1;
    return GetLastError() == ERROR_ALREADY_EXISTS && is_directory(path);
}

static void get_extension(const char *name, char *ext, size_t extSize) {
    const char *dot = strrchr(name, '.');
    if (!dot || dot == name) { if (extSize) ext[0] = '\0'; return; }
    safe_copy(ext, extSize, dot + 1);
    for (size_t i = 0; ext[i]; ++i) ext[i] = (char)tolower((unsigned char)ext[i]);
}

static int ext_is(const char *ext, const char *list) {
    char copy[512];
    safe_copy(copy, sizeof(copy), list);
    char *tok = strtok(copy, ",");
    while (tok) {
        if (_stricmp(ext, tok) == 0) return 1;
        tok = strtok(NULL, ",");
    }
    return 0;
}

static Category classify(const char *ext) {
    if (ext_is(ext, "jpg,jpeg,png,gif,bmp,webp,svg,ico,tif,tiff")) return CAT_IMAGES;
    if (ext_is(ext, "pdf,doc,docx,txt,rtf,xls,xlsx,ppt,pptx,csv,odt,ods,odp")) return CAT_DOCUMENTS;
    if (ext_is(ext, "mp4,mkv,avi,mov,wmv,flv,webm,m4v")) return CAT_VIDEOS;
    if (ext_is(ext, "mp3,wav,flac,aac,ogg,m4a,wma")) return CAT_AUDIO;
    if (ext_is(ext, "zip,rar,7z,tar,gz,bz2,xz")) return CAT_ARCHIVES;
    if (ext_is(ext, "exe,msi,bat,cmd,com")) return CAT_PROGRAMS;
    return CAT_OTHER;
}

static void reset_scan(void) {
    fileCount = 0;
    memset(categoryCounts, 0, sizeof(categoryCounts));
}

static void update_counts(void) {
    for (int i = 0; i < CAT_COUNT; ++i) {
        char text[32];
        snprintf(text, sizeof(text), "%d", categoryCounts[i]);
        SetWindowTextA(app.counts[i], text);
    }
    char total[32];
    snprintf(total, sizeof(total), "%d", fileCount);
    SetWindowTextA(app.total, total);
}

static void clear_list(void) {
    SendMessageA(app.fileList, LB_RESETCONTENT, 0, 0);
}

static void add_list_item(const char *name, Category cat) {
    char line[MAX_PATH_LEN + 128];
    snprintf(line, sizeof(line), "%s    ->    %s\\", name, categoryNames[cat]);
    SendMessageA(app.fileList, LB_ADDSTRING, 0, (LPARAM)line);
}

static void setStatusText(const char *text) {
    if (app.status) SetWindowTextA(app.status, text);
}

static int choose_folder(char *out, size_t outSize) {
    BROWSEINFOA bi;
    ZeroMemory(&bi, sizeof(bi));
    bi.hwndOwner = app.hwnd;
    bi.lpszTitle = "Select a folder to organize";
    bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE;
    PIDLIST_ABSOLUTE pidl = SHBrowseForFolderA(&bi);
    if (!pidl) return 0;
    BOOL ok = SHGetPathFromIDListA(pidl, out);
    CoTaskMemFree(pidl);
    if (ok && outSize) out[outSize - 1] = '\0';
    return ok ? 1 : 0;
}

static void scanFolder(void) {
    char folder[MAX_PATH_LEN];
    GetWindowTextA(app.folderEdit, folder, sizeof(folder));
    if (!folder[0]) { setStatusText("Select a folder first."); return; }
    if (!is_directory(folder)) { setStatusText("The selected folder does not exist."); return; }

    reset_scan();
    clear_list();

    char pattern[MAX_PATH_LEN];
    join_path(pattern, sizeof(pattern), folder, "*");

    WIN32_FIND_DATAA fd;
    HANDLE h = FindFirstFileA(pattern, &fd);
    if (h == INVALID_HANDLE_VALUE) {
        setStatusText("Could not scan the selected folder.");
        return;
    }

    do {
        if (fileCount >= MAX_FILES) break;
        if (!strcmp(fd.cFileName, ".") || !strcmp(fd.cFileName, "..")) continue;
        if (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) continue;
        if (fd.dwFileAttributes & FILE_ATTRIBUTE_HIDDEN) continue;

        FileItem *item = &files[fileCount];
        safe_copy(item->name, sizeof(item->name), fd.cFileName);
        join_path(item->source, sizeof(item->source), folder, item->name);

        char ext[64];
        get_extension(item->name, ext, sizeof(ext));
        item->category = classify(ext);
        categoryCounts[item->category]++;
        add_list_item(item->name, item->category);
        fileCount++;
    } while (FindNextFileA(h, &fd));

    FindClose(h);
    update_counts();

    char status[256];
    snprintf(status, sizeof(status), "Scan complete: %d file(s) found.", fileCount);
    setStatusText(status);
}

static void split_filename(const char *filename, char *base, size_t baseSize, char *ext, size_t extSize) {
    const char *dot = strrchr(filename, '.');
    if (dot && dot != filename) {
        size_t n = (size_t)(dot - filename);
        if (n >= baseSize) n = baseSize - 1;
        memcpy(base, filename, n);
        base[n] = '\0';
        safe_copy(ext, extSize, dot);
    } else {
        safe_copy(base, baseSize, filename);
        if (extSize) ext[0] = '\0';
    }
}

static void unique_destination(const char *dir, const char *filename, char *out, size_t outSize) {
    join_path(out, outSize, dir, filename);
    if (!is_regular_file(out)) return;

    char base[MAX_PATH], ext[128];
    split_filename(filename, base, sizeof(base), ext, sizeof(ext));
    for (int n = 1; n < 100000; ++n) {
        snprintf(out, outSize, "%s\\%s_%d%s", dir, base, n, ext);
        if (!is_regular_file(out)) return;
    }
    out[0] = '\0';
}

static int next_batch_id(void) {
    SYSTEMTIME st;
    GetLocalTime(&st);
    currentBatchId = ((unsigned long long)st.wYear * 100000000ULL) +
                     ((unsigned long long)st.wMonth * 1000000ULL) +
                     ((unsigned long long)st.wDay * 10000ULL) +
                     ((unsigned long long)st.wHour * 100ULL) +
                     st.wMinute;
    return 1;
}

static FILE *open_history(const char *mode) {
    CreateDirectoryA("data", NULL);
    return fopen("data\\history.log", mode);
}

static void append_history(unsigned long long batch, const char *source, const char *dest) {
    FILE *f = open_history("a");
    if (!f) return;
    fprintf(f, "%llu|%s|%s\n", batch, source, dest);
    fclose(f);
}

static void organizeFiles(void) {
    if (fileCount == 0) {
        MessageBoxA(app.hwnd, "Scan a folder before organizing.", APP_NAME, MB_OK | MB_ICONINFORMATION);
        return;
    }

    int answer = MessageBoxA(
        app.hwnd,
        "Files will be moved into category folders. Existing files will not be overwritten.\n\nContinue?",
        APP_NAME,
        MB_YESNO | MB_ICONQUESTION);
    if (answer != IDYES) return;

    char folder[MAX_PATH_LEN];
    GetWindowTextA(app.folderEdit, folder, sizeof(folder));
    if (!is_directory(folder)) { setStatusText("The selected folder no longer exists."); return; }

    next_batch_id();
    int moved = 0, failed = 0;

    for (int i = 0; i < fileCount; ++i) {
        FileItem *item = &files[i];
        char categoryDir[MAX_PATH_LEN];
        join_path(categoryDir, sizeof(categoryDir), folder, categoryNames[item->category]);

        if (!ensure_directory(categoryDir)) { failed++; continue; }

        char destination[MAX_PATH_LEN];
        unique_destination(categoryDir, item->name, destination, sizeof(destination));
        if (!destination[0]) { failed++; continue; }

        if (MoveFileExA(item->source, destination, MOVEFILE_COPY_ALLOWED)) {
            append_history(currentBatchId, item->source, destination);
            moved++;
        } else {
            failed++;
        }
    }

    char status[256];
    snprintf(status, sizeof(status), "Organization complete: %d moved, %d failed.", moved, failed);
    setStatusText(status);

    MessageBoxA(app.hwnd, status, APP_NAME, MB_OK | (failed ? MB_ICONWARNING : MB_ICONINFORMATION));
    scanFolder();
}

static int read_history(HistoryEntry **entries, unsigned long long **batches, size_t *count) {
    *entries = NULL; *batches = NULL; *count = 0;
    FILE *f = open_history("r");
    if (!f) return 0;

    char line[MAX_PATH_LEN * 2 + 128];
    while (fgets(line, sizeof(line), f)) {
        char *p1 = strchr(line, '|');
        if (!p1) continue;
        char *p2 = strchr(p1 + 1, '|');
        if (!p2) continue;
        *p1 = '\0'; *p2 = '\0';
        char *newline = strpbrk(p2 + 1, "\r\n");
        if (newline) *newline = '\0';

        unsigned long long batch = _strtoui64(line, NULL, 10);
        HistoryEntry *ne = realloc(*entries, (*count + 1) * sizeof(**entries));
        unsigned long long *nb = realloc(*batches, (*count + 1) * sizeof(**batches));
        if (!ne || !nb) { free(ne); free(nb); fclose(f); return 0; }
        *entries = ne; *batches = nb;
        safe_copy((*entries)[*count].source, sizeof((*entries)[*count].source), p1 + 1);
        safe_copy((*entries)[*count].destination, sizeof((*entries)[*count].destination), p2 + 1);
        (*batches)[*count] = batch;
        (*count)++;
    }
    fclose(f);
    return *count > 0;
}

static void undoLastBatch(void) {
    HistoryEntry *entries = NULL;
    unsigned long long *batches = NULL;
    size_t count = 0;
    if (!read_history(&entries, &batches, &count)) {
        MessageBoxA(app.hwnd, "No organization history was found.", APP_NAME, MB_OK | MB_ICONINFORMATION);
        return;
    }

    unsigned long long lastBatch = batches[count - 1];
    size_t start = count - 1;
    while (start > 0 && batches[start - 1] == lastBatch) start--;

    char question[256];
    snprintf(question, sizeof(question), "Undo the last organization?\n\nThis will restore %zu file(s).", count - start);
    if (MessageBoxA(app.hwnd, question, APP_NAME, MB_YESNO | MB_ICONQUESTION) != IDYES) {
        free(entries); free(batches); return;
    }

    int restored = 0, failed = 0;
    for (size_t i = start; i < count; ++i) {
        if (!is_regular_file(entries[i].destination)) { failed++; continue; }
        if (is_regular_file(entries[i].source)) { failed++; continue; }
        if (MoveFileExA(entries[i].destination, entries[i].source, MOVEFILE_COPY_ALLOWED)) restored++;
        else failed++;
    }

    FILE *f = open_history("w");
    if (f) {
        for (size_t i = 0; i < start; ++i)
            fprintf(f, "%llu|%s|%s\n", batches[i], entries[i].source, entries[i].destination);
        fclose(f);
    }

    free(entries); free(batches);

    char status[256];
    snprintf(status, sizeof(status), "Undo complete: %d restored, %d failed.", restored, failed);
    setStatusText(status);
    MessageBoxA(app.hwnd, status, APP_NAME, MB_OK | (failed ? MB_ICONWARNING : MB_ICONINFORMATION));
    scanFolder();
}

static HFONT make_font(int size, int weight) {
    return CreateFontA(size, 0, 0, 0, weight, FALSE, FALSE, FALSE,
                       DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                       CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_DONTCARE, "Segoe UI");
}

static HWND make_label(HWND parent, const char *text, int x, int y, int w, int h, HFONT font) {
    HWND hWnd = CreateWindowExA(0, "STATIC", text, WS_CHILD | WS_VISIBLE,
                                x, y, w, h, parent, NULL, GetModuleHandleA(NULL), NULL);
    SendMessageA(hWnd, WM_SETFONT, (WPARAM)font, TRUE);
    return hWnd;
}

static HWND make_button(HWND parent, const char *text, int id, int x, int y, int w, int h) {
    HWND hWnd = CreateWindowExA(0, "BUTTON", text,
                                WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_PUSHBUTTON,
                                x, y, w, h, parent, (HMENU)(INT_PTR)id,
                                GetModuleHandleA(NULL), NULL);
    SendMessageA(hWnd, WM_SETFONT, (WPARAM)app.boldFont, TRUE);
    return hWnd;
}

static void create_gui(HWND hwnd) {
    app.normalFont = make_font(16, FW_NORMAL);
    app.boldFont = make_font(16, FW_SEMIBOLD);
    app.titleFont = make_font(27, FW_BOLD);

    make_label(hwnd, APP_NAME, 30, 22, 500, 38, app.titleFont);
    make_label(hwnd, "Native Windows desktop file organizer", 32, 58, 500, 25, app.normalFont);

    make_label(hwnd, "Folder", 35, 105, 100, 25, app.boldFont);
    app.folderEdit = CreateWindowExA(WS_EX_CLIENTEDGE, "EDIT", "",
                                     WS_CHILD | WS_VISIBLE | WS_TABSTOP | ES_AUTOHSCROLL,
                                     35, 135, 560, 36, hwnd, (HMENU)ID_FOLDER_EDIT,
                                     GetModuleHandleA(NULL), NULL);
    SendMessageA(app.folderEdit, WM_SETFONT, (WPARAM)app.normalFont, TRUE);

    make_button(hwnd, "Browse...", ID_BROWSE, 605, 135, 105, 36);
    make_button(hwnd, "Scan", ID_SCAN, 720, 135, 75, 36);

    make_label(hwnd, "FILE SUMMARY", 35, 200, 250, 30, app.titleFont);

    const int ys[CAT_COUNT] = {250, 285, 320, 355, 390, 425, 460};
    for (int i = 0; i < CAT_COUNT; ++i) {
        make_label(hwnd, categoryNames[i], 40, ys[i], 130, 25, app.normalFont);
        app.counts[i] = make_label(hwnd, "0", 180, ys[i], 70, 25, app.boldFont);
    }
    make_label(hwnd, "TOTAL", 40, 500, 130, 25, app.boldFont);
    app.total = make_label(hwnd, "0", 180, 500, 70, 25, app.boldFont);

    make_label(hwnd, "FILES TO ORGANIZE", 300, 200, 300, 30, app.titleFont);
    app.fileList = CreateWindowExA(WS_EX_CLIENTEDGE, "LISTBOX", "",
                                   WS_CHILD | WS_VISIBLE | WS_VSCROLL | WS_HSCROLL | LBS_NOINTEGRALHEIGHT,
                                   300, 235, 565, 265, hwnd, (HMENU)ID_LIST,
                                   GetModuleHandleA(NULL), NULL);
    SendMessageA(app.fileList, WM_SETFONT, (WPARAM)app.normalFont, TRUE);

    make_button(hwnd, "Organize Files", ID_ORGANIZE, 300, 525, 180, 45);
    make_button(hwnd, "Undo Last Organization", ID_UNDO, 495, 525, 200, 45);

    make_label(hwnd, "Status", 35, 575, 80, 25, app.boldFont);
    app.status = make_label(hwnd, "Ready. Select a folder to begin.", 95, 575, 770, 25, app.normalFont);
}

static LRESULT CALLBACK window_proc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_CREATE:
            app.hwnd = hwnd;
            create_gui(hwnd);
            return 0;

        case WM_COMMAND:
            switch (LOWORD(wParam)) {
                case ID_BROWSE: {
                    char folder[MAX_PATH_LEN];
                    if (choose_folder(folder, sizeof(folder))) {
                        SetWindowTextA(app.folderEdit, folder);
                        setStatusText("Folder selected. Press Scan.");
                    }
                    return 0;
                }
                case ID_SCAN:
                    scanFolder();
                    return 0;
                case ID_ORGANIZE:
                    organizeFiles();
                    return 0;
                case ID_UNDO:
                    undoLastBatch();
                    return 0;
            }
            break;

        case WM_CTLCOLORSTATIC: {
            HDC dc = (HDC)wParam;
            SetBkColor(dc, CLR_BG);
            SetTextColor(dc, CLR_TEXT);
            static HBRUSH brush = NULL;
            if (!brush) brush = CreateSolidBrush(CLR_BG);
            return (LRESULT)brush;
        }

        case WM_DESTROY:
            DeleteObject(app.normalFont);
            DeleteObject(app.boldFont);
            DeleteObject(app.titleFont);
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcA(hwnd, msg, wParam, lParam);
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    (void)hPrevInstance; (void)lpCmdLine;

    WNDCLASSA wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.lpfnWndProc = window_proc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME;
    wc.hCursor = LoadCursorA(NULL, IDC_ARROW);
    wc.hbrBackground = CreateSolidBrush(CLR_BG);
    wc.style = CS_HREDRAW | CS_VREDRAW;

    if (!RegisterClassA(&wc)) {
        MessageBoxA(NULL, "Could not register the application window.", APP_NAME, MB_OK | MB_ICONERROR);
        return 1;
    }

    HWND hwnd = CreateWindowExA(
        0, CLASS_NAME, APP_NAME,
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 900, 670,
        NULL, NULL, hInstance, NULL);

    if (!hwnd) {
        MessageBoxA(NULL, "Could not create the application window.", APP_NAME, MB_OK | MB_ICONERROR);
        return 1;
    }

    ShowWindow(hwnd, nCmdShow);
    UpdateWindow(hwnd);

    MSG msg;
    while (GetMessageA(&msg, NULL, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageA(&msg);
    }
    return (int)msg.wParam;
}
