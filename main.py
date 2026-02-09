from core.run import RunProgram

run = RunProgram()


def main() -> None:
    try:
        run.save_json_data('config_files', 'device_list', run.device_list)
        run.create_directories()
        run.get_logging_data()
        run.start_stream()
        run.create_wrapped_threads()
        run.stop_stream()
    except Exception as e:
        run.logger.error(f'Проверка выдала ошибку: {e}\nНажми Enter для завершения.')


if __name__ == '__main__':
    main()
