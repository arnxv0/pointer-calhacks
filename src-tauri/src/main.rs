#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[cfg(target_os = "macos")]
#[macro_use]
extern crate objc;

use tauri::{Manager, Emitter};
use tauri::menu::{Menu, MenuItem};
use tauri::tray::{TrayIconBuilder};
use tauri_plugin_shell::ShellExt;

#[cfg(target_os = "macos")]
use cocoa::appkit::{NSWindow, NSWindowStyleMask};
#[cfg(target_os = "macos")]
use cocoa::base::id;
#[cfg(target_os = "macos")]
use objc::runtime::YES;

#[cfg(target_os = "macos")]
fn apply_macos_window_effects(window: &tauri::WebviewWindow) {
    use cocoa::appkit::NSWindowTitleVisibility;
    use cocoa::base::nil;
    
    let window_label = window.label().to_string();
    let app_handle = window.app_handle().clone();
    
    window.run_on_main_thread(move || {
        if let Some(window) = app_handle.get_webview_window(&window_label) {
            unsafe {
                let ns_window = window.ns_window().unwrap() as id;
                
                // Enable rounded corners
                ns_window.setTitlebarAppearsTransparent_(YES);
                ns_window.setTitleVisibility_(NSWindowTitleVisibility::NSWindowTitleHidden);
                
                let mut style_mask = ns_window.styleMask();
                style_mask.insert(NSWindowStyleMask::NSFullSizeContentViewWindowMask);
                ns_window.setStyleMask_(style_mask);
                
                // CRITICAL: Make window background transparent to avoid black corners
                let _: () = msg_send![ns_window, setOpaque: 0];
                let clear_color: id = msg_send![class!(NSColor), clearColor];
                let _: () = msg_send![ns_window, setBackgroundColor: clear_color];
                
                // Also make sure the content view background is transparent
                let content_view: id = ns_window.contentView();
                let _: () = msg_send![content_view, setWantsLayer: 1];
                let layer: id = msg_send![content_view, layer];
                if !layer.is_null() {
                    let _: () = msg_send![layer, setBackgroundColor: nil];
                }
            }
        }
    }).ok();
}

#[tauri::command]
fn set_custom_cursor() -> Result<String, String> {
    Ok("Cursor set".to_string())
}

#[tauri::command]
fn show_settings(app: tauri::AppHandle) -> Result<String, String> {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.set_focus();
        Ok("Settings shown".to_string())
    } else {
        Err("Settings window not found".to_string())
    }
}

#[tauri::command]
async fn show_overlay(
    app: tauri::AppHandle,
    x: f64,
    y: f64,
    context: serde_json::Value,
) -> Result<String, String> {
    println!("📍 Showing overlay at: ({}, {})", x, y);
    
    if let Some(window) = app.get_webview_window("overlay") {
        let _ = window.destroy();
    }
    
    use tauri::webview::WebviewWindowBuilder;
    
    // Overlay dimensions
    let overlay_width = 600.0;
    let overlay_height = 80.0;
    
    // Get screen size
    let monitor = match app.primary_monitor() {
        Ok(Some(m)) => m,
        _ => {
            // Fallback: use default position without bounds checking
            println!("⚠️ Could not get monitor info, using unbounded position");
            let overlay = WebviewWindowBuilder::new(
                &app,
                "overlay",
                tauri::WebviewUrl::App("index.html#overlay".into())
            )
            .title("Pointer Overlay")
            .inner_size(overlay_width, overlay_height)
            .position(x - (overlay_width / 2.0), y)
            .decorations(false)
            .transparent(true)
            .always_on_top(true)
            .resizable(false)
            .skip_taskbar(true)
            .visible(false)
            .content_protected(false)
            .build();
            
            match overlay {
                Ok(window) => {
                    #[cfg(target_os = "macos")]
                    apply_macos_window_effects(&window);
                    
                    let _ = window.emit("overlay-context", context);
                    std::thread::sleep(std::time::Duration::from_millis(50));
                    let _ = window.show();
                    let _ = window.set_focus();
                    return Ok("Overlay shown".to_string());
                }
                Err(e) => return Err(format!("Failed to create overlay: {}", e)),
            }
        }
    };
    
    let screen_size = monitor.size();
    let screen_width = screen_size.width as f64;
    let screen_height = screen_size.height as f64;
    
    // Buffer zones
    let left_buffer = 20.0;
    let right_buffer = 20.0;
    let top_buffer = 40.0;  // For menu bar
    let bottom_buffer = 100.0;  // For dock bar
    
    // Calculate centered position around cursor
    let mut overlay_x = x - (overlay_width / 2.0);
    let mut overlay_y = y;
    
    // Constrain X position within screen bounds
    if overlay_x < left_buffer {
        overlay_x = left_buffer;
    } else if overlay_x + overlay_width > screen_width - right_buffer {
        overlay_x = screen_width - overlay_width - right_buffer;
    }
    
    // Constrain Y position within screen bounds
    if overlay_y < top_buffer {
        overlay_y = top_buffer;
    } else if overlay_y + overlay_height > screen_height - bottom_buffer {
        overlay_y = screen_height - overlay_height - bottom_buffer;
    }
    
    println!("📍 Adjusted overlay position to: ({}, {})", overlay_x, overlay_y);
    
    let overlay = WebviewWindowBuilder::new(
        &app,
        "overlay",
        tauri::WebviewUrl::App("index.html#overlay".into())
    )
    .title("Pointer Overlay")
    .inner_size(overlay_width, overlay_height)
    .position(overlay_x, overlay_y)
    .decorations(false)
    .transparent(true)
    .always_on_top(true)
    .resizable(false)
    .skip_taskbar(true)
    .visible(false)
    .content_protected(false)
    .build();
    
    match overlay {
        Ok(window) => {
            #[cfg(target_os = "macos")]
            apply_macos_window_effects(&window);
            
            let _ = window.emit("overlay-context", context);
            std::thread::sleep(std::time::Duration::from_millis(50));
            let _ = window.show();
            let _ = window.set_focus();
            Ok("Overlay shown".to_string())
        }
        Err(e) => Err(format!("Failed to create overlay: {}", e)),
    }
}

#[tauri::command]
async fn hide_overlay(app: tauri::AppHandle) -> Result<String, String> {
    if let Some(window) = app.get_webview_window("overlay") {
        let _ = window.close();
    }
    Ok("Overlay hidden".to_string())
}

#[tauri::command]
fn process_query(query: String, mode: String, _settings: serde_json::Value) -> Result<String, String> {
    Ok(format!("Processing query: {} in mode: {}", query, mode))
}

#[tauri::command]
fn load_settings() -> Result<serde_json::Value, String> {
    Ok(serde_json::json!({}))
}

#[tauri::command]
fn save_settings(_settings: serde_json::Value) -> Result<String, String> {
    Ok("Settings saved".to_string())
}

#[tauri::command]
async fn start_backend(app: tauri::AppHandle) -> Result<String, String> {
    println!("🚀 Starting Python backend...");
    
    match app.shell().sidecar("pointer-backend") {
        Ok(sidecar_command) => {
            match sidecar_command.spawn() {
                Ok((mut rx, _child)) => {
                    println!("✅ Backend process spawned successfully");
                    
                    // Spawn a task to read and print backend output
                    tauri::async_runtime::spawn(async move {
                        use tauri_plugin_shell::process::CommandEvent;
                        while let Some(event) = rx.recv().await {
                            match event {
                                CommandEvent::Stdout(line) => {
                                    print!("[Backend] {}", String::from_utf8_lossy(&line));
                                }
                                CommandEvent::Stderr(line) => {
                                    eprint!("[Backend Error] {}", String::from_utf8_lossy(&line));
                                }
                                CommandEvent::Error(err) => {
                                    eprintln!("[Backend Process Error] {}", err);
                                }
                                CommandEvent::Terminated(payload) => {
                                    println!("[Backend] Process terminated with code: {:?}", payload.code);
                                    break;
                                }
                                _ => {}
                            }
                        }
                    });
                    
                    Ok("Backend started".to_string())
                }
                Err(e) => {
                    let err_msg = format!("Failed to spawn backend: {}", e);
                    eprintln!("❌ {}", err_msg);
                    Err(err_msg)
                }
            }
        }
        Err(e) => {
            let err_msg = format!("Failed to create sidecar command: {}", e);
            eprintln!("❌ {}", err_msg);
            Err(err_msg)
        }
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Create system tray menu
            let settings_item = MenuItem::with_id(app, "settings", "Settings", true, None::<&str>)?;
            let quit_item = MenuItem::with_id(app, "quit", "Quit Pointer", true, None::<&str>)?;
            
            let menu = Menu::with_items(app, &[&settings_item, &quit_item])?;
            
            // Create tray icon
            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        "settings" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                        "quit" => {
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .build(app)?;
            
            // Prevent app from quitting when main window closes
            if let Some(main_window) = app.get_webview_window("main") {
                #[cfg(target_os = "macos")]
                apply_macos_window_effects(&main_window);
                
                let window_clone = main_window.clone();
                main_window.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        let _ = window_clone.hide();
                    }
                });
            }
            
            // Auto-start Python backend in the background
            let app_handle = app.handle().clone();
            std::thread::spawn(move || {
                // Give the app a moment to fully initialize
                std::thread::sleep(std::time::Duration::from_millis(500));
                
                println!("🔄 Attempting to auto-start backend...");
                tauri::async_runtime::block_on(async move {
                    match start_backend(app_handle).await {
                        Ok(_) => println!("✅ Backend auto-started successfully"),
                        Err(e) => eprintln!("⚠️  Failed to auto-start backend: {}", e),
                    }
                });
            });
            
            println!("✅ Pointer running in menu bar");
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            set_custom_cursor,
            show_settings,
            show_overlay,
            hide_overlay,
            process_query,
            load_settings,
            save_settings,
            start_backend
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
