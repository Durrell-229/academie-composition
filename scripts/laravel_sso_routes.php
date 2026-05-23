<?php

/**
 * ====================================================================
 * SSO Laravel → Django (Académie Numérique)
 * ====================================================================
 * 
 * Ce fichier contient les routes API nécessaires pour permettre
 * l'authentification unique (SSO) entre l'app Laravel et la plateforme Django.
 * 
 * PRÉ-REQUIS :
 * - Laravel Sanctum installé : composer require laravel/sanctum
 * - Migration Sanctum exécutée : php artisan vendor:publish --provider="Laravel\Sanctum\SanctumServiceProvider"
 * - php artisan migrate
 * 
 * FONCTIONNEMENT :
 * 1. L'utilisateur se connecte sur Laravel
 * 2. Un lien "Accéder à Académie" le redirige vers Django avec son token
 * 3. Django vérifie le token via ces routes API et connecte automatiquement l'utilisateur
 * 
 * URL Django : https://academie-composition.onrender.com/accounts/laravel-sso/?token={TOKEN}
 */

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use App\Models\User;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
*/

// Vérifier un token Sanctum et retourner les infos du user
// Django appelle cette route quand un utilisateur arrive via le lien SSO
Route::post('/auth/check-token', function (Request $request) {
    $request->validate(['token' => 'required|string']);

    // Vérification via Laravel Sanctum
    $user = User::whereHas('tokens', function ($query) use ($request) {
        $query->where('token', hash('sha256', $request->token));
    })->first();

    // ALTERNATIVE si tu n'utilises PAS Sanctum mais un simple api_token :
    // $user = User::where('api_token', $request->token)->first();

    if (!$user) {
        return response()->json([
            'error' => 'Token invalide ou expiré',
        ], 401);
    }

    return response()->json([
        'id' => $user->id,
        'email' => $user->email,
        'first_name' => $user->first_name ?? '',
        'last_name' => $user->last_name ?? '',
        'name' => $user->name ?? $user->first_name . ' ' . $user->last_name,
        'role' => $user->role ?? $user->getLaravelRole(), // adapte selon ton modèle
    ]);
});

// Login avec email/password et retourne un token Sanctum
// Utilisé si Django doit authentifier directement via credentials
Route::post('/auth/verify', function (Request $request) {
    $request->validate([
        'email' => 'required|email',
        'password' => 'required',
    ]);

    if (!Auth::attempt($request->only('email', 'password'))) {
        return response()->json([
            'error' => 'Identifiants invalides',
        ], 401);
    }

    $user = Auth::user();

    // Créer un token Sanctum pour cette session
    $token = $user->createToken('django-sso')->plainTextToken;

    return response()->json([
        'id' => $user->id,
        'email' => $user->email,
        'first_name' => $user->first_name ?? '',
        'last_name' => $user->last_name ?? '',
        'name' => $user->name ?? $user->first_name . ' ' . $user->last_name,
        'role' => $user->role ?? $user->getLaravelRole(),
        'token' => $token,
    ]);
});

// Invalider un token (quand l'utilisateur se déconnecte de Laravel)
Route::post('/auth/logout', function (Request $request) {
    $request->validate(['token' => 'required|string']);

    $user = User::whereHas('tokens', function ($query) use ($request) {
        $query->where('token', hash('sha256', $request->token));
    })->first();

    if ($user) {
        // Révoquer le token spécifique
        $user->tokens()->where('token', hash('sha256', $request->token))->delete();
    }

    return response()->json(['message' => 'Déconnexion réussie']);
})->middleware('auth:sanctum');
