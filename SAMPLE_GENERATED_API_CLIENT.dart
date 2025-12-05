// This is a sample of what the generated Dart API client looks like
// with cache interceptor support enabled

import 'package:dio/dio.dart';
import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';
import '../models/models.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  final dynamic body;

  ApiException({
    required this.statusCode,
    required this.message,
    this.body,
  });

  @override
  String toString() => 'ApiException(statusCode: $statusCode, message: $message)';
}

class RetryInterceptor extends Interceptor {
  final int maxRetries;
  final int retryDelayMs;
  final List<int> retryableStatusCodes;

  RetryInterceptor({
    this.maxRetries = 3,
    this.retryDelayMs = 1000,
    this.retryableStatusCodes = const [500, 502, 503, 504],
  });

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    // Only retry on specific conditions
    if (!_shouldRetry(err)) {
      return handler.next(err);
    }

    // Get retry count from request extra data
    final retryCount = err.requestOptions.extra['retryCount'] as int? ?? 0;

    if (retryCount >= maxRetries) {
      return handler.next(err);
    }

    // Calculate exponential backoff delay
    final delayMs = retryDelayMs * (1 << retryCount); // 2^retryCount

    // Wait before retrying
    await Future.delayed(Duration(milliseconds: delayMs));

    // Clone request options and increment retry count
    final newOptions = err.requestOptions.copyWith(
      extra: {
        ...err.requestOptions.extra,
        'retryCount': retryCount + 1,
      },
    );

    // Retry the request
    try {
      final dio = Dio();
      dio.options = err.requestOptions.copyWith() as BaseOptions;
      final response = await dio.fetch(newOptions);
      return handler.resolve(response);
    } on DioException catch (e) {
      return handler.next(e);
    }
  }

  bool _shouldRetry(DioException err) {
    // Only retry idempotent requests (GET, HEAD, PUT, DELETE, OPTIONS, TRACE)
    final method = err.requestOptions.method.toUpperCase();
    final isIdempotent = ['GET', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'TRACE'].contains(method);

    if (!isIdempotent) {
      return false;
    }

    // Check if it's a network error (no response from server)
    if (err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.connectionError) {
      return true;
    }

    // Check if status code is retryable (5xx errors)
    final statusCode = err.response?.statusCode;
    if (statusCode != null && retryableStatusCodes.contains(statusCode)) {
      return true;
    }

    return false;
  }
}

class AuthInterceptor extends Interceptor {
  final String token;

  AuthInterceptor(this.token);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers['Authorization'] = 'Bearer $token';
    super.onRequest(options, handler);
  }
}

// Cache Interceptor Configuration
// To enable response caching, pass a CacheStore instance to the ApiClient constructor.
// Example with MemCacheStore (in-memory caching):
//
//   final cacheStore = MemCacheStore();
//   final apiClient = ApiClient(
//     dio,
//     cacheStore: cacheStore,
//   );
//
// The cache uses the following configuration:
//   - maxStale: 300 seconds (how long responses are cached)
//   - policy: CachePolicy.request (respects HTTP cache headers)
//   - priority: CachePriority.normal
//   - hitCacheOnErrorExcept: [401, 403] (use cache on errors except auth failures)
//
// For persistent caching, use HiveCacheStore:
//   - Add hive_flutter dependency to pubspec.yaml
//   - Initialize: await Hive.initFlutter();
//   - Create store: final cacheStore = HiveCacheStore(await HiveStore.open());

class ApiClient {
  final Dio _dio;
  final Map<String, String> _defaultHeaders;
  final Duration? connectTimeout;
  final Duration? receiveTimeout;
  final Duration? sendTimeout;

  ApiClient(
    this._dio,
    {
      String? token,
      bool enableLogging = false,
      CacheStore? cacheStore,  // ← NEW: Optional cache store parameter
      Map<String, String>? defaultHeaders,
      this.connectTimeout = const Duration(seconds: 30),
      this.receiveTimeout = const Duration(seconds: 30),
      this.sendTimeout = const Duration(seconds: 30),
    }
  ) : _defaultHeaders = defaultHeaders ?? {} {
    _dio.interceptors.add(LogInterceptor(
      requestBody: enableLogging,
      responseBody: enableLogging,
      requestHeader: enableLogging,
      responseHeader: false,
      error: true,
      logPrint: (object) => print('[API] $object'),
    ));
    _dio.interceptors.add(RetryInterceptor(
      maxRetries: 3,
      retryDelayMs: 1000,
      retryableStatusCodes: [500, 502, 503, 504],
    ));
    if (token != null) {
      _dio.interceptors.add(AuthInterceptor(token));
    }
    // ↓ NEW: Cache interceptor setup
    if (cacheStore != null) {
      _dio.interceptors.add(DioCacheInterceptor(
        options: CacheOptions(
          store: cacheStore,
          maxStale: const Duration(seconds: 300),
          policy: CachePolicy.request,
          priority: CachePriority.normal,
          hitCacheOnErrorExcept: [401, 403],
        ),
      ));
    }
  }

  /// Get a user by ID
  ///
  /// * [id] - Path parameter
  Future<User> getUser(String id, {Map<String, String>? headers, Duration? requestTimeout, CancelToken? cancelToken}) async {
    try {
      final mergedHeaders = {..._defaultHeaders, ...?headers};
      final response = await _dio.get('users/$id', options: Options(headers: mergedHeaders, sendTimeout: requestTimeout ?? sendTimeout, receiveTimeout: requestTimeout ?? receiveTimeout), cancelToken: cancelToken);
      return User.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(
        statusCode: e.response?.statusCode ?? 0,
        message: e.message ?? 'Unknown error',
        body: e.response?.data,
      );
    }
  }
}
