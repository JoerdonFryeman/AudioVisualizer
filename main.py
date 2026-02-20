import signal
from core.run import RunProgram

run = RunProgram()


def main(name: str, version: str, year: int) -> None:
    """Запускающая все процессы главная функция."""

    def get_handler(signum, frame) -> None:
        run.running = False
        run.logger.info('Задействован обработчик сигналов для корректного завершения: %s', signum)

    handler_tuple: tuple[str, str, str] = ('SIGHUP', 'SIGINT', 'SIGTERM')
    for name in handler_tuple:
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), get_handler)

    try:
        run.create_directories()
        run.get_logging_data()
        run.log_app_release(name=name, version=version, year=year)
        run.start_stream()
        run.create_wrapped_threads()
        run.stop_stream()
    except Exception as e:
        run.logger.exception(f'Проверка выдала ошибку: {e}\nЕсли не был выполнен выход в терминал, нажми Enter.')
        try:
            run.running = False
            run.stop_stream()
        except Exception:
            run.logger.exception('Не удалось корректно остановить аудиострим!')


if __name__ == '__main__':
    main('AudioVisualizer', '1.0.1', 2026)
